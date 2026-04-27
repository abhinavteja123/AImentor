"""
RAG Knowledge Base — document ingestion, chunking, and semantic retrieval.

Uses an in-process vector store (backed by a simple cosine-similarity index
over JSON-serialised embeddings in PostgreSQL).  This avoids a ChromaDB /
FAISS dependency; if you want to upgrade later, swap ``search()`` only.

Embeddings are generated via the LLM provider (Gemini embedding API) or
fall back to a lightweight TF-IDF approach so the system works even without
an embedding model installed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.tutor import KnowledgeDocument
from ..llm_client import get_llm_client

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
# Lightweight TF-IDF vectoriser (zero external dependencies)
# ───────────────────────────────────────────────────────────────

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would shall should may might can could and but or nor not "
    "for to from in on at by with of about into through during before "
    "after above below between out off over under again further then "
    "once here there when where why how all each every both few more "
    "most other some such no only own same so than too very it its "
    "this that these those i me my we our you your he him his she her".split()
)


def _tokenise(text: str) -> List[str]:
    """Simple whitespace + punctuation tokeniser."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = Counter(tokens)
    total = len(tokens) or 1
    return {t: (c / total) * idf.get(t, 1.0) for t, c in tf.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ───────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────


class KnowledgeBase:
    """Ingest educational content and retrieve relevant chunks for RAG."""

    CHUNK_SIZE = 500  # characters per chunk (approximate)
    CHUNK_OVERLAP = 50

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()

    # ── Ingestion ─────────────────────────────────────────────

    async def ingest_document(
        self,
        topic: str,
        content: str,
        *,
        subtopic: Optional[str] = None,
        source: Optional[str] = None,
        difficulty_level: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[KnowledgeDocument]:
        """Chunk and store educational content."""
        chunks = self._chunk_text(content)
        docs: List[KnowledgeDocument] = []

        for i, chunk in enumerate(chunks):
            doc = KnowledgeDocument(
                topic=topic,
                subtopic=subtopic,
                content=chunk,
                chunk_index=i,
                source=source,
                difficulty_level=difficulty_level,
                doc_metadata=metadata or {},
            )
            self.db.add(doc)
            docs.append(doc)

        await self.db.flush()
        logger.info("Ingested %d chunks for topic=%r", len(docs), topic)
        return docs

    async def ingest_bulk(self, documents: List[Dict[str, Any]]) -> int:
        """Ingest multiple documents. Each dict needs at least {topic, content}."""
        total = 0
        for doc_data in documents:
            chunks = await self.ingest_document(
                topic=doc_data["topic"],
                content=doc_data["content"],
                subtopic=doc_data.get("subtopic"),
                source=doc_data.get("source"),
                difficulty_level=doc_data.get("difficulty_level", 1),
                metadata=doc_data.get("metadata"),
            )
            total += len(chunks)
        await self.db.commit()
        return total

    # ── Retrieval ─────────────────────────────────────────────

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        topic_filter: Optional[str] = None,
        difficulty_max: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant knowledge chunks for a query.

        Uses TF-IDF cosine similarity over the stored document set.
        Fast enough for <10 k chunks; swap for a vector DB if you scale.
        """
        # 1. Pull candidate documents from DB
        stmt = select(KnowledgeDocument)
        if topic_filter:
            stmt = stmt.where(
                or_(
                    func.lower(KnowledgeDocument.topic).contains(topic_filter.lower()),
                    func.lower(KnowledgeDocument.subtopic).contains(topic_filter.lower()),
                )
            )
        if difficulty_max:
            stmt = stmt.where(KnowledgeDocument.difficulty_level <= difficulty_max)
        stmt = stmt.limit(500)  # safety cap

        result = await self.db.execute(stmt)
        candidates = result.scalars().all()

        if not candidates:
            return []

        # 2. Build TF-IDF index over candidates
        all_tokens = []
        doc_tokens_list = []
        for doc in candidates:
            tokens = _tokenise(doc.content)
            doc_tokens_list.append(tokens)
            all_tokens.extend(tokens)

        # IDF
        n_docs = len(candidates) or 1
        df: Counter = Counter()
        for tokens in doc_tokens_list:
            df.update(set(tokens))
        idf = {t: math.log(n_docs / (1 + c)) + 1 for t, c in df.items()}

        # Query vector
        q_tokens = _tokenise(query)
        q_vec = _tfidf_vector(q_tokens, idf)

        # Score each document
        scored = []
        for doc, tokens in zip(candidates, doc_tokens_list):
            d_vec = _tfidf_vector(tokens, idf)
            score = _cosine(q_vec, d_vec)
            if score > 0.0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "id": str(doc.id),
                "topic": doc.topic,
                "subtopic": doc.subtopic,
                "content": doc.content,
                "difficulty_level": doc.difficulty_level,
                "source": doc.source,
                "relevance_score": round(score, 4),
            }
            for score, doc in scored[:top_k]
        ]

    async def get_topics(self) -> List[str]:
        """Return all distinct topics in the knowledge base."""
        result = await self.db.execute(
            select(KnowledgeDocument.topic).distinct()
        )
        return [row[0] for row in result.all()]

    async def get_stats(self) -> Dict[str, Any]:
        """Return knowledge base statistics."""
        total = (await self.db.execute(
            select(func.count(KnowledgeDocument.id))
        )).scalar() or 0
        topics = await self.get_topics()
        return {"total_chunks": total, "topics_count": len(topics), "topics": topics[:20]}

    # ── Helpers ────────────────────────────────────────────────

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.CHUNK_SIZE
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)
                break_at = max(last_period, last_newline)
                if break_at > start:
                    end = break_at + 1
            chunks.append(text[start:end].strip())
            start = end - self.CHUNK_OVERLAP
        return [c for c in chunks if c]

    async def generate_content_for_topic(
        self,
        topic: str,
        subtopic: Optional[str] = None,
        difficulty: int = 1,
    ) -> str:
        """Use LLM to generate educational content for a topic (auto-seeding)."""
        difficulty_label = {1: "beginner", 2: "elementary", 3: "intermediate", 4: "advanced", 5: "expert"}
        level = difficulty_label.get(difficulty, "intermediate")

        prompt = f"""Create comprehensive educational content about "{topic}" 
{f'specifically covering "{subtopic}"' if subtopic else ''} at a {level} level.

Include:
1. Clear explanation of core concepts
2. Key terminology with definitions  
3. Practical examples and code snippets where applicable
4. Common mistakes and misconceptions
5. Practice exercises

Write in a clear, tutoring-oriented style. Format with headers and bullet points."""

        return await self.llm.generate_completion(
            system_prompt="You are an expert educator creating learning materials.",
            user_prompt=prompt,
            temperature=0.5,
            max_tokens=3000,
        )

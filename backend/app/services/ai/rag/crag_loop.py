"""
CRAG (Corrective Retrieval-Augmented Generation) Loop.

Implements Algorithm 1 from the paper:
  1. Retrieve top-k chunks from FAISS
  2. Score relevance via LLM evaluator → confidence ∈ [0,1]
  3. Action: CORRECT (≥0.6) / AMBIGUOUS (0.3-0.6) / INCORRECT (<0.3)
  4. Decompose chunks → strip irrelevant sentences
  5. Recompose: return filtered context
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional

from ..llm_client import get_llm_client

logger = logging.getLogger(__name__)


class RetrievalAction(Enum):
    CORRECT = "correct"
    AMBIGUOUS = "ambiguous"
    INCORRECT = "incorrect"


# AI syllabus unit summaries — fallback when retrieval is INCORRECT
UNIT_SUMMARIES = {
    "Agents & ML Intro": (
        "Intelligent agents perceive their environment through sensors and act upon it through actuators. "
        "Machine learning enables agents to improve performance through experience. Key concepts include "
        "rational agents, PEAS framework, and types of learning: supervised, unsupervised, reinforcement."
    ),
    "Search & CSP": (
        "Search algorithms explore state spaces to find solutions. Uninformed search includes BFS and DFS. "
        "Informed search uses heuristics (A*, greedy best-first). Constraint satisfaction problems define "
        "variables, domains, and constraints. Arc consistency and backtracking are key solving techniques."
    ),
    "Knowledge Representation": (
        "Knowledge representation uses formal logic to encode information about the world. Propositional logic "
        "uses boolean connectives. First-order logic adds quantifiers and predicates. Semantic networks, "
        "frames, and ontologies provide structured representations for AI reasoning systems."
    ),
    "Planning & Heuristics": (
        "Planning algorithms create sequences of actions to achieve goals from initial states. STRIPS and PDDL "
        "define planning languages. Forward and backward search, partial-order planning, and graph-plan are "
        "key approaches. Admissible heuristics guarantee optimal solutions in A* search."
    ),
    "Learning & Game AI": (
        "Machine learning systems improve through experience. Supervised learning maps inputs to outputs. "
        "Reinforcement learning maximizes cumulative reward through trial and error. Game-playing AI uses "
        "minimax with alpha-beta pruning. Monte Carlo tree search powers modern game AI like AlphaGo."
    ),
}


class CRAGLoop:
    """
    Corrective RAG with 3-action self-critique loop.

    τ_correct = 0.6  → CORRECT: use retrieved chunks directly
    τ_ambiguous = 0.3 → AMBIGUOUS: re-query with expanded terms
    < 0.3             → INCORRECT: fallback to unit summary
    """

    def __init__(self, knowledge_base, threshold_correct: float = 0.6,
                 threshold_ambiguous: float = 0.3):
        self.kb = knowledge_base
        self.llm = get_llm_client()
        self.τ_correct = threshold_correct
        self.τ_ambiguous = threshold_ambiguous

    async def retrieve_and_correct(self, query: str,
                                    topic_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Algorithm 1: CRAG-Tutor Retrieval Loop.
        Returns: {context, action, confidence, chunks_used}
        """
        # Step 1: Retrieve top-k chunks
        chunks = await self.kb.search(query, top_k=5, topic_filter=topic_filter)

        if not chunks:
            return {
                "context": self._get_best_summary(query),
                "action": RetrievalAction.INCORRECT.value,
                "confidence": 0.0,
                "chunks_used": 0,
            }

        # Step 2: Score relevance of retrieved chunks
        confidence = await self._evaluate_relevance(query, chunks)

        # Step 3: Determine action
        if confidence >= self.τ_correct:
            action = RetrievalAction.CORRECT
            context = await self._decompose_recompose(query, chunks)

        elif confidence >= self.τ_ambiguous:
            action = RetrievalAction.AMBIGUOUS
            # Re-query with expanded terms
            expanded = self._expand_query(query)
            chunks2 = await self.kb.search(expanded, top_k=5, topic_filter=topic_filter)
            all_chunks = chunks + [c for c in chunks2 if c["id"] not in {ch["id"] for ch in chunks}]
            context = await self._decompose_recompose(query, all_chunks)

        else:
            action = RetrievalAction.INCORRECT
            context = self._get_best_summary(query)

        logger.info("CRAG: action=%s confidence=%.3f chunks=%d",
                     action.value, confidence, len(chunks))

        return {
            "context": context,
            "action": action.value,
            "confidence": round(confidence, 4),
            "chunks_used": len(chunks),
        }

    async def _evaluate_relevance(self, query: str, chunks: List[Dict]) -> float:
        """Score chunk relevance using LLM as evaluator (replaces T5 in paper)."""
        chunk_texts = "\n---\n".join([c["content"][:300] for c in chunks[:3]])
        prompt = f"""Rate how relevant these retrieved chunks are to the student's query.

QUERY: {query}

RETRIEVED CHUNKS:
{chunk_texts}

Return ONLY a JSON object: {{"relevance_score": 0.0-1.0, "reasoning": "brief explanation"}}
Score 0.0 = completely irrelevant, 1.0 = perfectly relevant."""

        try:
            result = await self.llm.generate_json(
                "You are a relevance evaluator for an educational retrieval system. Return only JSON.",
                prompt)
            return float(result.get("relevance_score", 0.5))
        except Exception:
            # Fallback: use the search scores themselves
            avg_score = sum(c.get("relevance_score", 0) for c in chunks) / len(chunks)
            return min(1.0, avg_score * 2)  # scale up since TF-IDF scores are small

    async def _decompose_recompose(self, query: str, chunks: List[Dict]) -> str:
        """Strip irrelevant sentences from chunks (paper Section 5.1.2 step 4-5)."""
        all_text = "\n".join([c["content"] for c in chunks])
        sentences = re.split(r'(?<=[.!?])\s+', all_text)

        if len(sentences) <= 8:
            return all_text

        # Use LLM to filter relevant sentences
        prompt = f"""Given a student's question, select ONLY the sentences that are directly relevant.

QUESTION: {query}

SENTENCES (numbered):
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(sentences[:20]))}

Return ONLY the numbers of relevant sentences as JSON: {{"relevant": [1, 3, 5, ...]}}"""

        try:
            result = await self.llm.generate_json(
                "You are a relevance filter. Return only JSON with relevant sentence numbers.", prompt)
            relevant_ids = result.get("relevant", list(range(1, min(9, len(sentences) + 1))))
            filtered = [sentences[i-1] for i in relevant_ids if 0 < i <= len(sentences)]
            return " ".join(filtered[:8]) if filtered else all_text[:1000]
        except Exception:
            return " ".join(sentences[:8])

    def _expand_query(self, query: str) -> str:
        """Simple query expansion with AI glossary synonyms."""
        expansions = {
            "search": "search algorithm pathfinding BFS DFS A-star",
            "agent": "intelligent agent rational agent BDI PEAS",
            "learning": "machine learning training classification regression",
            "neural": "neural network deep learning backpropagation",
            "tree": "decision tree search tree binary tree",
            "graph": "graph traversal adjacency BFS DFS shortest path",
            "logic": "propositional logic first-order predicate",
            "planning": "STRIPS PDDL goal state action planning",
            "heuristic": "heuristic admissible A-star informed search",
            "game": "minimax alpha-beta pruning game tree MCTS",
            "constraint": "CSP constraint satisfaction arc consistency backtracking",
            "probability": "Bayesian probability inference Bayes theorem",
        }
        words = query.lower().split()
        extra = " ".join(expansions.get(w, "") for w in words if w in expansions)
        return f"{query} {extra}".strip()

    def _get_best_summary(self, query: str) -> str:
        """Get the most relevant unit summary as fallback."""
        query_lower = query.lower()
        best_match = ""
        best_score = 0
        for unit_name, summary in UNIT_SUMMARIES.items():
            # Simple keyword overlap
            unit_words = set(unit_name.lower().split())
            query_words = set(query_lower.split())
            overlap = len(unit_words & query_words)
            if overlap > best_score:
                best_score = overlap
                best_match = summary
        return best_match or list(UNIT_SUMMARIES.values())[0]

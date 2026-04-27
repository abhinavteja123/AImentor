"""
AgentRAG-Tutor API Endpoints

Provides:
  POST /ask              — Student asks question → agentic RAG response + follow-up
  POST /answer           — Student answers follow-up → BKT update + RL reward
  GET  /knowledge-state  — Full BKT knowledge state dashboard
  GET  /next-question    — RL-selected adaptive question
  POST /knowledge-base/ingest  — Upload educational content
  GET  /knowledge-base/stats   — KB statistics
  POST /knowledge-base/generate — Auto-generate content via LLM
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.postgres import get_db
from ...schemas.tutor import (
    TutorAskRequest, TutorAskResponse,
    TutorAnswerRequest, TutorAnswerResponse,
    KnowledgeStateResponse, KBStatsResponse,
    KnowledgeIngestRequest, BulkIngestRequest,
    GenerateContentRequest,
)
from ...services.ai.tutor_engine import TutorEngine
from ...services.ai.rag.knowledge_base import KnowledgeBase
from ...utils.security import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


def _wrap_500(exc: Exception, op: str) -> HTTPException:
    """
    Convert an unexpected exception into a 500 with a server-side trace id.

    Logs the full traceback under WARN with a short trace id; the client
    sees only the trace id so we never leak internals (DB strings, stack
    frames, secrets) to the response body.
    """
    trace_id = uuid.uuid4().hex[:12]
    logger.exception("[tutor.%s] trace=%s — %s", op, trace_id, exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Tutor {op} failed (trace={trace_id}). Please retry; if this persists, share the trace id.",
    )


@router.post("/ask", response_model=TutorAskResponse)
async def tutor_ask(
    request: TutorAskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Student asks a question.
    
    The agentic RAG pipeline:
    1. Retrieves relevant knowledge from the KB
    2. Generates explanation with retrieved context
    3. Self-evaluates and refines if needed
    4. Generates an adaptive follow-up question (RL-selected difficulty)
    """
    try:
        engine = TutorEngine(db)
        return await engine.ask(
            user_id=current_user.id,
            question=request.question,
            topic=request.topic,
            session_id=request.session_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise _wrap_500(e, "ask")


@router.post("/answer", response_model=TutorAnswerResponse)
async def tutor_answer(
    request: TutorAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Student answers a follow-up question.
    
    Pipeline:
    1. LLM evaluates the answer
    2. BKT updates skill mastery
    3. RL updates reward for the difficulty/type arm
    4. Returns next adaptive question
    """
    try:
        engine = TutorEngine(db)
        return await engine.answer(
            user_id=current_user.id,
            question_text=request.question_text,
            student_answer=request.student_answer,
            topic=request.topic,
            difficulty=request.difficulty,
            question_type=request.question_type,
            response_time_seconds=request.response_time_seconds,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise _wrap_500(e, "answer")


@router.get("/knowledge-state", response_model=KnowledgeStateResponse)
async def get_knowledge_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the student's full BKT knowledge state (mastery per skill)."""
    try:
        engine = TutorEngine(db)
        return await engine.get_knowledge_state(current_user.id)
    except Exception as e:
        raise _wrap_500(e, "knowledge-state")


@router.get("/next-question")
async def get_next_question(
    topic: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the next RL-selected adaptive question."""
    try:
        engine = TutorEngine(db)
        return await engine.get_next_question(current_user.id, topic)
    except Exception as e:
        raise _wrap_500(e, "next-question")


@router.post("/knowledge-base/ingest")
async def ingest_knowledge(
    request: KnowledgeIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload educational content to the knowledge base."""
    try:
        kb = KnowledgeBase(db)
        docs = await kb.ingest_document(
            topic=request.topic, content=request.content,
            subtopic=request.subtopic, source=request.source,
            difficulty_level=request.difficulty_level)
        await db.commit()
        return {"message": f"Ingested {len(docs)} chunks", "chunks": len(docs)}
    except Exception as e:
        raise _wrap_500(e, "kb-ingest")


@router.post("/knowledge-base/bulk-ingest")
async def bulk_ingest(
    request: BulkIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk upload multiple documents."""
    try:
        kb = KnowledgeBase(db)
        total = await kb.ingest_bulk([d.model_dump() for d in request.documents])
        return {"message": f"Ingested {total} chunks", "total_chunks": total}
    except Exception as e:
        raise _wrap_500(e, "kb-bulk-ingest")


@router.get("/knowledge-base/stats", response_model=KBStatsResponse)
async def kb_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base statistics."""
    try:
        kb = KnowledgeBase(db)
        return await kb.get_stats()
    except Exception as e:
        raise _wrap_500(e, "kb-stats")


@router.post("/knowledge-base/generate")
async def generate_content(
    request: GenerateContentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate educational content for a topic using LLM and ingest it."""
    try:
        kb = KnowledgeBase(db)
        content = await kb.generate_content_for_topic(
            request.topic, request.subtopic, request.difficulty)
        docs = await kb.ingest_document(
            topic=request.topic, content=content,
            subtopic=request.subtopic, difficulty_level=request.difficulty,
            source="ai-generated", metadata={"generator": "llm"})
        await db.commit()
        return {"message": f"Generated and ingested {len(docs)} chunks",
                "chunks": len(docs), "content_preview": content[:500]}
    except Exception as e:
        raise _wrap_500(e, "kb-generate")

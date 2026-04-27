"""
Pydantic schemas for the AgentRAG-Tutor endpoints.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ── Request schemas ──────────────────────────────────────────

class TutorAskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Student's question")
    topic: Optional[str] = Field(None, description="Topic filter for RAG retrieval")
    session_id: Optional[str] = None


class TutorAnswerRequest(BaseModel):
    question_text: str = Field(..., description="The question that was asked")
    student_answer: str = Field(..., min_length=1)
    topic: Optional[str] = None
    difficulty: int = Field(1, ge=1, le=5)
    question_type: str = "short_answer"
    response_time_seconds: int = Field(0, ge=0)


class KnowledgeIngestRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    content: str = Field(..., min_length=10)
    subtopic: Optional[str] = None
    source: Optional[str] = None
    difficulty_level: int = Field(1, ge=1, le=5)


class BulkIngestRequest(BaseModel):
    documents: List[KnowledgeIngestRequest]


class GenerateContentRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    subtopic: Optional[str] = None
    difficulty: int = Field(1, ge=1, le=5)


# ── Response schemas ─────────────────────────────────────────

class FollowUpQuestion(BaseModel):
    question: str = ""
    correct_answer: str = ""
    difficulty: int = 1
    question_type: str = "short_answer"
    topic: str = ""
    hints: List[str] = []
    explanation: str = ""
    distractors: Optional[List[str]] = None


class CRAGInfo(BaseModel):
    """CRAG retrieval loop results (Paper Algorithm 1)."""
    action: str = "correct"              # correct / ambiguous / incorrect
    confidence: float = 0.0              # relevance score [0,1]
    chunks_used: int = 0                 # number of retrieved chunks


class EvaluationInfo(BaseModel):
    quality_score: float = 1.0
    was_refined: bool = False


class DifficultySelection(BaseModel):
    difficulty: int
    question_type: str
    epsilon: float = 0.0
    exploration: bool = False
    # "ppo" when the trained policy chose; "mab" for epsilon-greedy fallback
    # (no checkpoint loaded, or off-curriculum question).
    selector: Literal["ppo", "mab"] = "mab"


class TutorAskResponse(BaseModel):
    response: str
    follow_up_question: Dict[str, Any] = {}
    crag: CRAGInfo = CRAGInfo()
    evaluation: EvaluationInfo = EvaluationInfo()
    difficulty_selection: DifficultySelection = DifficultySelection(difficulty=1, question_type="short_answer")
    current_mastery: Optional[float] = None
    # Paper-aligned 5-KC fields (Paper Section 5.2.2).
    kc_id: Optional[int] = None
    kc_name: Optional[str] = None
    course_key: Optional[str] = None       # "ai_fundamentals" | "operating_systems" | None
    course_name: Optional[str] = None
    mastery_vector: Optional[List[float]] = None
    session_id: str = ""

    class Config:
        from_attributes = True


class BKTInfo(BaseModel):
    mastery_before: float
    mastery_after: float
    is_mastered: bool
    kc_id: Optional[int] = None
    course_key: Optional[str] = None


class AnswerEvaluation(BaseModel):
    is_correct: bool = False
    partial_credit: float = 0.0
    feedback: str = ""
    correct_answer: str = ""


class TutorAnswerResponse(BaseModel):
    evaluation: Dict[str, Any] = {}
    bkt: Optional[Dict[str, Any]] = None
    next_question: Dict[str, Any] = {}
    next_difficulty: Dict[str, Any] = {}
    kc_id: Optional[int] = None
    kc_name: Optional[str] = None
    course_key: Optional[str] = None
    course_name: Optional[str] = None
    mastery_vector: Optional[List[float]] = None
    encouragement: str = ""

    class Config:
        from_attributes = True


class SkillMasteryItem(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    p_mastery: float
    is_mastered: bool
    attempts: int
    correct_count: int
    accuracy: float
    consecutive_correct: int
    last_updated: Optional[str] = None


class MasterySummary(BaseModel):
    total_skills_tracked: int = 0
    mastered_count: int = 0
    in_progress_count: int = 0
    average_mastery: float = 0.0
    overall_readiness: float = 0.0


class KCMastery(BaseModel):
    """Per-KC mastery row for the dashboard radar (Paper Section 5.2.2)."""
    kc_id: int
    kc_name: str
    p_mastery: float
    is_mastered: bool
    attempts: int = 0
    # Multi-course paper extension. Optional for backwards-compat with older
    # serialised payloads; new code always populates these.
    course_key: Optional[str] = None
    course_name: Optional[str] = None


class KnowledgeStateResponse(BaseModel):
    summary: MasterySummary = MasterySummary()
    skills: List[Dict[str, Any]] = []
    weakest_skills: List[Dict[str, Any]] = []
    kc_mastery: List[KCMastery] = []


class KBStatsResponse(BaseModel):
    total_chunks: int = 0
    topics_count: int = 0
    topics: List[str] = []

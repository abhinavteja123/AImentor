"""
AgentRAG-Tutor Models — Knowledge State, Questions, Responses, RL Policy.

Supports: Bayesian Knowledge Tracing (BKT), adaptive question selection,
and reinforcement-learning-based difficulty control.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Float, Text, Boolean, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database.postgres import Base


class KnowledgeDocument(Base):
    """Educational content stored for RAG retrieval."""

    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(String(255), nullable=False, index=True)
    subtopic = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    source = Column(String(500), nullable=True)  # URL or file origin
    difficulty_level = Column(Integer, default=1)  # 1-5
    doc_metadata = Column("metadata", JSONB, nullable=True)  # tags, language, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeDocument {self.topic}:{self.chunk_index}>"


class KnowledgeState(Base):
    """BKT per-skill mastery state for each student."""

    __tablename__ = "knowledge_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills_master.id", ondelete="CASCADE"), nullable=False, index=True)

    # BKT parameters (per user-skill pair)
    p_mastery = Column(Float, default=0.1)   # P(student knows this skill)
    p_init = Column(Float, default=0.1)      # Prior probability of mastery
    p_learn = Column(Float, default=0.3)     # Probability of learning per attempt
    p_guess = Column(Float, default=0.25)    # Probability of correct guess
    p_slip = Column(Float, default=0.1)      # Probability of incorrect despite mastery

    # Tracking
    attempts = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)
    consecutive_incorrect = Column(Integer, default=0)

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="knowledge_states")
    skill = relationship("SkillMaster", backref="knowledge_states")

    def __repr__(self):
        return f"<KnowledgeState user={self.user_id} skill={self.skill_id} mastery={self.p_mastery:.2f}>"


class TutorQuestion(Base):
    """Question bank for adaptive tutoring."""

    __tablename__ = "tutor_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills_master.id", ondelete="CASCADE"), nullable=True, index=True)
    topic = Column(String(255), nullable=False, index=True)

    difficulty = Column(Integer, default=1)  # 1-5
    question_type = Column(String(50), default="multiple_choice")  # multiple_choice, short_answer, code_exercise, open_ended
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    distractors = Column(JSONB, nullable=True)  # For MC: ["wrong1", "wrong2", "wrong3"]
    explanation = Column(Text, nullable=True)   # Shown after answering
    hints = Column(JSONB, nullable=True)        # Progressive hints
    tags = Column(JSONB, nullable=True)         # ["python", "loops", "beginner"]

    # AI-generated flag
    is_ai_generated = Column(Boolean, default=False)
    times_served = Column(Integer, default=0)
    avg_correct_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    skill = relationship("SkillMaster", backref="tutor_questions")

    def __repr__(self):
        return f"<TutorQuestion {self.topic} diff={self.difficulty}>"


class StudentResponse(Base):
    """Record of every student answer — feeds BKT updates."""

    __tablename__ = "student_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("tutor_questions.id", ondelete="SET NULL"), nullable=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills_master.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)

    student_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    response_time_seconds = Column(Integer, nullable=True)
    difficulty_at_time = Column(Integer, nullable=True)

    # BKT snapshot
    bkt_mastery_before = Column(Float, nullable=True)
    bkt_mastery_after = Column(Float, nullable=True)

    # AI evaluation details
    evaluation_feedback = Column(Text, nullable=True)
    partial_credit = Column(Float, nullable=True)  # 0.0 - 1.0 for partial correctness

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="student_responses")
    question = relationship("TutorQuestion", backref="student_responses")

    def __repr__(self):
        return f"<StudentResponse user={self.user_id} correct={self.is_correct}>"


class RLPolicyState(Base):
    """RL agent state per user — stores Q-values / bandit arms."""

    __tablename__ = "rl_policy_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Multi-Armed Bandit state: {arm_key: {count, total_reward, avg_reward}}
    bandit_state = Column(JSONB, default=dict)

    # Optional Q-table: {state_key: {action_key: q_value}}
    q_table = Column(JSONB, nullable=True)

    # Exploration rate
    epsilon = Column(Float, default=0.3)
    total_interactions = Column(Integer, default=0)

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="rl_policy_state")

    def __repr__(self):
        return f"<RLPolicyState user={self.user_id} interactions={self.total_interactions}>"

"""
Unit tests for MentorChatEngine that exercise the Postgres-backed path
without a live database. We stub AsyncSession with a minimal fake.

End-to-end tests against real Postgres will be added in test_integration_chat.py
once DB connectivity is restored.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.services.ai.chat_engine import MentorChatEngine, _parse_uuid


# -------------------- _parse_uuid --------------------


def test_parse_uuid_accepts_valid_string():
    u = uuid4()
    assert _parse_uuid(str(u)) == u


def test_parse_uuid_returns_none_on_garbage():
    assert _parse_uuid("not-a-uuid") is None
    assert _parse_uuid("") is None
    assert _parse_uuid(None) is None  # type: ignore[arg-type]


# -------------------- _analyze_intent (pure function) --------------------


@pytest.fixture
def engine_without_db():
    """MentorChatEngine with a stubbed db + stubbed llm (neither is hit here)."""
    fake_db = SimpleNamespace()
    fake_llm = SimpleNamespace()
    # Bypass __init__ so it doesn't touch get_llm_client() / build chain.
    e = object.__new__(MentorChatEngine)
    e.db = fake_db
    e.llm = fake_llm
    return e


@pytest.mark.parametrize(
    "message,expected",
    [
        ("I'm stuck on recursion", "asking_for_help"),
        ("Can you explain decorators?", "requesting_explanation"),
        ("I'm tired and giving up", "seeking_motivation"),
        ("This is really difficult", "reporting_struggle"),
        ("What should I do next?", "asking_next_steps"),
        ("Any tutorial for hooks?", "requesting_resources"),
        ("How am I doing?", "asking_progress"),
        ("hi there", "general_chat"),
    ],
)
async def test_analyze_intent(engine_without_db, message, expected):
    assert await engine_without_db._analyze_intent(message, {}) == expected


# -------------------- _generate_suggestions --------------------


async def test_generate_suggestions_caps_at_three(engine_without_db):
    out = await engine_without_db._generate_suggestions({}, "asking_next_steps")
    assert len(out) <= 3
    assert all(s["action"] for s in out)


async def test_generate_suggestions_includes_roadmap(engine_without_db):
    out = await engine_without_db._generate_suggestions({}, "general_chat")
    actions = {s["action"] for s in out}
    assert "view_roadmap" in actions


# -------------------- persistence layer with fake session --------------------


class _FakeSession:
    """Minimal async SQLAlchemy-ish session tracking what happened."""

    def __init__(self, preloaded=None):
        self._store: dict = dict(preloaded or {})
        self.added: list = []
        self.deleted: list = []
        self.commits: int = 0
        self.rollbacks: int = 0

    async def get(self, model, pk):
        return self._store.get(pk)

    def add(self, obj):
        self.added.append(obj)
        self._store[obj.id] = obj

    async def delete(self, obj):
        self.deleted.append(obj)
        self._store.pop(obj.id, None)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


async def test_save_conversation_creates_new_session_on_first_message(engine_without_db):
    engine_without_db.db = _FakeSession()
    sid = str(uuid4())
    uid = uuid4()
    await engine_without_db._save_conversation(
        session_id=sid,
        user_id=uid,
        user_message="hi",
        assistant_message="hello",
        context_used={"intent": "general_chat"},
    )
    assert len(engine_without_db.db.added) == 1
    created = engine_without_db.db.added[0]
    assert created.id == UUID(sid)
    assert created.user_id == uid
    assert len(created.messages) == 2
    assert created.messages[0]["role"] == "user"
    assert created.messages[1]["role"] == "assistant"
    assert engine_without_db.db.commits == 1


async def test_save_conversation_appends_to_existing(engine_without_db):
    sid = uuid4()
    existing = SimpleNamespace(
        id=sid,
        user_id=uuid4(),
        title="old",
        messages=[{"role": "user", "content": "prev"}],
        updated_at=datetime.utcnow(),
    )
    engine_without_db.db = _FakeSession(preloaded={sid: existing})
    await engine_without_db._save_conversation(
        session_id=str(sid),
        user_id=existing.user_id,
        user_message="again",
        assistant_message="still here",
        context_used={"intent": "general_chat"},
    )
    assert engine_without_db.db.added == []  # no new row
    assert len(existing.messages) == 3  # prev + user + assistant
    assert engine_without_db.db.commits == 1


async def test_save_conversation_silently_skips_invalid_session_id(engine_without_db):
    engine_without_db.db = _FakeSession()
    await engine_without_db._save_conversation(
        session_id="not-a-uuid",
        user_id=uuid4(),
        user_message="x",
        assistant_message="y",
        context_used={},
    )
    assert engine_without_db.db.added == []
    assert engine_without_db.db.commits == 0


async def test_get_chat_history_returns_last_n(engine_without_db):
    sid = uuid4()
    existing = SimpleNamespace(
        id=sid,
        messages=[{"role": "user", "content": f"m{i}"} for i in range(15)],
    )
    engine_without_db.db = _FakeSession(preloaded={sid: existing})
    out = await engine_without_db._get_chat_history(str(sid), limit=5)
    assert [m["content"] for m in out] == ["m10", "m11", "m12", "m13", "m14"]


async def test_get_chat_history_empty_when_invalid_id(engine_without_db):
    engine_without_db.db = _FakeSession()
    assert await engine_without_db._get_chat_history("garbage", limit=5) == []


async def test_get_session_returns_none_when_user_mismatch(engine_without_db):
    sid = uuid4()
    owner = uuid4()
    other = uuid4()
    existing = SimpleNamespace(
        id=sid, user_id=owner, title="x", messages=[],
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    engine_without_db.db = _FakeSession(preloaded={sid: existing})
    assert await engine_without_db.get_session(str(sid), other) is None
    result = await engine_without_db.get_session(str(sid), owner)
    assert result is not None
    assert result["session_id"] == str(sid)


async def test_delete_session_respects_ownership(engine_without_db):
    sid = uuid4()
    owner = uuid4()
    other = uuid4()
    existing = SimpleNamespace(id=sid, user_id=owner)
    engine_without_db.db = _FakeSession(preloaded={sid: existing})

    # Wrong owner → nothing happens
    await engine_without_db.delete_session(str(sid), other)
    assert engine_without_db.db.deleted == []

    # Correct owner → deletes + commits
    await engine_without_db.delete_session(str(sid), owner)
    assert engine_without_db.db.deleted == [existing]
    assert engine_without_db.db.commits == 1

"""
Deterministic tests for the AgentRAG-Tutor runtime — no DB or network.

Coverage:
- ``kc_mapping.resolve_kc_from_topic`` routing accuracy (multi-course):
  AI Fundamentals KCs, Operating Systems KCs, off-curriculum, isolation.
- ``bkt_service.bkt_update`` math (single-step + multi-step convergence).
- ``BKTService.MASTERY_THRESHOLD`` matches paper Section 5.2.3.
- ``ppo_agent.get_ppo_agent`` lazy loading + graceful MAB fallback.
- Course registry invariants: 2 courses × 5 KCs, lexically disjoint.

Run from repo root:
    python -m pytest backend/research/tests/test_tutor_runtime.py -v
"""

from __future__ import annotations

import os
import pytest


# ── KC routing — AI Fundamentals course ────────────────────────

@pytest.mark.parametrize("topic, expected", [
    # KC1
    ("PEAS framework for agents",            ("ai_fundamentals", 1)),
    ("rational reflex agent",                 ("ai_fundamentals", 1)),
    # KC2
    ("Explain A* search",                    ("ai_fundamentals", 2)),
    ("BFS vs DFS",                           ("ai_fundamentals", 2)),
    ("constraint satisfaction problem",       ("ai_fundamentals", 2)),
    ("minimax with alpha-beta pruning",       ("ai_fundamentals", 2)),
    # KC3
    ("Bayesian inference",                   ("ai_fundamentals", 3)),
    ("first-order predicate logic",          ("ai_fundamentals", 3)),
    ("modus ponens proof",                   ("ai_fundamentals", 3)),
    # KC4
    ("STRIPS planning",                      ("ai_fundamentals", 4)),
    ("PDDL action schema",                   ("ai_fundamentals", 4)),
    ("partial-order planning",               ("ai_fundamentals", 4)),
    # KC5
    ("Q-learning update",                    ("ai_fundamentals", 5)),
    ("Monte Carlo tree search",              ("ai_fundamentals", 5)),
    ("decision tree algorithm",              ("ai_fundamentals", 5)),
])
def test_resolve_ai_fundamentals(topic, expected):
    from backend.app.services.ai.bkt.kc_mapping import resolve_kc_from_topic
    assert resolve_kc_from_topic(topic) == expected


# ── KC routing — Operating Systems course ──────────────────────

@pytest.mark.parametrize("topic, expected", [
    # OS-KC1
    ("Explain context switch in processes",  ("operating_systems", 1)),
    ("fork and exec system calls",            ("operating_systems", 1)),
    ("thread pool design",                    ("operating_systems", 1)),
    # OS-KC2
    ("round robin scheduling",                ("operating_systems", 2)),
    ("preemptive vs non-preemptive scheduler", ("operating_systems", 2)),
    ("MLFQ priority queues",                  ("operating_systems", 2)),
    # OS-KC3
    ("Explain page table walk",               ("operating_systems", 3)),
    ("TLB miss handling",                     ("operating_systems", 3)),
    ("LRU page replacement",                  ("operating_systems", 3)),
    # OS-KC4
    ("semaphore vs mutex",                    ("operating_systems", 4)),
    ("deadlock prevention algorithms",        ("operating_systems", 4)),
    ("readers writers problem",               ("operating_systems", 4)),
    # OS-KC5
    ("inode structure in ext4",               ("operating_systems", 5)),
    ("RAID levels",                           ("operating_systems", 5)),
    ("journaling file system",                ("operating_systems", 5)),
])
def test_resolve_operating_systems(topic, expected):
    from backend.app.services.ai.bkt.kc_mapping import resolve_kc_from_topic
    assert resolve_kc_from_topic(topic) == expected


# ── Off-curriculum + cross-course isolation ────────────────────

@pytest.mark.parametrize("topic", [
    "How do Docker volumes work?",
    "React useState hook",
    "Build me a SQL CTE",
    "",
])
def test_off_curriculum_returns_none(topic):
    from backend.app.services.ai.bkt.kc_mapping import resolve_kc_from_topic
    assert resolve_kc_from_topic(topic) is None


def test_bfs_dfs_route_to_ai_not_os():
    """BFS/DFS appear in AI Fundamentals (Search & CSP) and must not be
    hijacked by Operating Systems even though OS has 'process'/'thread' nearby."""
    from backend.app.services.ai.bkt.kc_mapping import resolve_kc_from_topic
    assert resolve_kc_from_topic("Compare BFS and DFS") == ("ai_fundamentals", 2)
    assert resolve_kc_from_topic("uniform cost search") == ("ai_fundamentals", 2)


def test_paging_routes_to_os_not_ai():
    """Paging is OS-KC3; must not collide with any AI keyword."""
    from backend.app.services.ai.bkt.kc_mapping import resolve_kc_from_topic
    assert resolve_kc_from_topic("demand paging and thrashing") == ("operating_systems", 3)


# ── Registry invariants ────────────────────────────────────────

def test_registry_has_two_courses():
    from backend.app.services.ai.bkt.kc_mapping import COURSE_REGISTRY
    assert set(COURSE_REGISTRY.keys()) == {"ai_fundamentals", "operating_systems"}


def test_each_course_has_five_kcs():
    from backend.app.services.ai.bkt.kc_mapping import COURSE_REGISTRY
    for course_key, course in COURSE_REGISTRY.items():
        assert len(course.kcs) == 5, f"{course_key} should have exactly 5 KCs"
        assert set(course.kcs.keys()) == {1, 2, 3, 4, 5}


def test_keyword_disjointness_across_courses():
    """No keyword should belong to two different courses (would cause routing ties)."""
    from backend.app.services.ai.bkt.kc_mapping import COURSE_REGISTRY
    seen: dict[str, str] = {}
    for course_key, course in COURSE_REGISTRY.items():
        for spec in course.kcs.values():
            for kw in spec.keywords:
                if kw in seen and seen[kw] != course_key:
                    pytest.fail(
                        f"Keyword {kw!r} appears in both {seen[kw]} and {course_key}")
                seen[kw] = course_key


def test_get_bkt_params_per_course():
    from backend.app.services.ai.bkt.kc_mapping import get_bkt_params
    ai_kc2 = get_bkt_params("ai_fundamentals", 2)
    os_kc4 = get_bkt_params("operating_systems", 4)
    assert ai_kc2 == {"p_l0": 0.20, "p_t": 0.15, "p_g": 0.20, "p_s": 0.10}
    assert os_kc4 == {"p_l0": 0.15, "p_t": 0.12, "p_g": 0.18, "p_s": 0.12}
    assert get_bkt_params("nonexistent_course", 1) is None
    assert get_bkt_params("ai_fundamentals", 99) is None


# ── BKT update math ────────────────────────────────────────────

def test_bkt_update_correct_increases_mastery():
    from backend.app.services.ai.bkt.bkt_service import bkt_update
    p0 = 0.30
    p1 = bkt_update(p0, is_correct=True, p_learn=0.20, p_guess=0.20, p_slip=0.10)
    assert p1 > p0
    assert 0.0 < p1 < 1.0


def test_bkt_update_incorrect_decreases_posterior():
    from backend.app.services.ai.bkt.bkt_service import bkt_update
    p0 = 0.70
    p1 = bkt_update(p0, is_correct=False, p_learn=0.0, p_guess=0.20, p_slip=0.10)
    assert p1 < p0


def test_bkt_update_clipped_to_open_interval():
    from backend.app.services.ai.bkt.bkt_service import bkt_update
    p = 0.5
    for _ in range(50):
        p = bkt_update(p, True, p_learn=0.3, p_guess=0.25, p_slip=0.10)
    assert 0.0 < p < 1.0


def test_bkt_converges_under_paper_kc2_params():
    from backend.app.services.ai.bkt.bkt_service import bkt_update
    from backend.app.services.ai.bkt.bkt_tracker import BKT_PARAMS
    p = BKT_PARAMS[2]["p_l0"]  # 0.20
    for _ in range(30):
        p = bkt_update(p, True, BKT_PARAMS[2]["p_t"], BKT_PARAMS[2]["p_g"], BKT_PARAMS[2]["p_s"])
    assert p >= 0.95


def test_mastery_threshold_matches_paper():
    from backend.app.services.ai.bkt.bkt_service import BKTService
    from backend.app.services.ai.bkt.bkt_tracker import MASTERY_THRESHOLD as PAPER
    assert BKTService.MASTERY_THRESHOLD == PAPER == 0.95


# ── PPO singleton + fallback ───────────────────────────────────

def test_ppo_agent_falls_back_to_mab_when_checkpoint_missing(tmp_path, monkeypatch):
    from backend.app.services.ai.adaptive import ppo_agent as mod
    monkeypatch.setenv("PPO_MODEL_PATH", str(tmp_path / "does-not-exist.zip"))
    mod.reset_ppo_agent()
    agent = mod.get_ppo_agent()
    assert agent.is_ppo_active is False
    d = agent.select_difficulty(mastery_vector=[0.3, 0.3, 0.3, 0.3, 0.3], session_step=0)
    assert d in {1, 2, 3, 4, 5}


@pytest.mark.skipif(
    not os.path.exists("backend/models/ppo_agent/final_model.zip"),
    reason="PPO checkpoint not present — train via train_ppo_tutor.ipynb first.",
)
def test_ppo_agent_loads_real_checkpoint():
    from backend.app.services.ai.adaptive import ppo_agent as mod
    os.environ["PPO_MODEL_PATH"] = "backend/models/ppo_agent/final_model.zip"
    mod.reset_ppo_agent()
    agent = mod.get_ppo_agent()
    assert agent.is_ppo_active is True
    d = agent.select_difficulty(mastery_vector=[0.3, 0.3, 0.3, 0.3, 0.3], session_step=0)
    assert d in {1, 2, 3, 4, 5}


# ── Schema selector + course fields ────────────────────────────

def test_difficulty_selection_selector_default():
    from backend.app.schemas.tutor import DifficultySelection
    sel = DifficultySelection(difficulty=3, question_type="short_answer")
    assert sel.selector == "mab"


def test_tutor_ask_response_carries_course_fields():
    from backend.app.schemas.tutor import TutorAskResponse
    resp = TutorAskResponse(
        response="x", kc_id=2, kc_name="Search & CSP",
        course_key="ai_fundamentals", course_name="AI Fundamentals",
        mastery_vector=[0.2, 0.2, 0.3, 0.2, 0.1],
    )
    assert resp.course_key == "ai_fundamentals"
    assert resp.kc_id == 2
    assert resp.mastery_vector and len(resp.mastery_vector) == 5


def test_kc_mastery_carries_course_fields():
    from backend.app.schemas.tutor import KCMastery
    m = KCMastery(kc_id=4, kc_name="Concurrency & Synchronization",
                  course_key="operating_systems", course_name="Operating Systems",
                  p_mastery=0.42, is_mastered=False, attempts=3)
    assert m.course_key == "operating_systems"
    assert m.attempts == 3

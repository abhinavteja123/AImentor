"""
Course + KC mapping — runtime registry for paper-aligned domains.

The IEEE paper defines 5 fixed Knowledge Components per *course*. To support
multi-domain validation (AI Fundamentals + Operating Systems), this module
holds a `COURSE_REGISTRY` keyed by ``course_key``. Each course defines:

* its 5 KCs (id, name, keyword set)
* per-KC BKT parameters (paper Section 5.2.2 Table 2 conventions)
* the ``skills_master.category`` value used to identify its anchor rows

``resolve_kc_from_topic(text)`` returns ``(course_key, kc_id)`` or ``None``;
off-curriculum topics still return ``None`` and bypass BKT/PPO.

Keyword sets across courses MUST be lexically disjoint to keep routing
unambiguous (verified by ``test_tutor_runtime`` cross-course isolation tests).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.skill import SkillMaster


# ── Course / KC dataclasses ──────────────────────────────────


@dataclass(frozen=True)
class KCSpec:
    """One Knowledge Component within a course."""
    kc_id: int
    name: str
    keywords: Set[str]
    p_l0: float       # prior mastery (paper Table 2)
    p_t: float        # learn rate
    p_g: float        # guess rate
    p_s: float        # slip rate

    def as_params_dict(self) -> Dict[str, float]:
        return {"p_l0": self.p_l0, "p_t": self.p_t, "p_g": self.p_g, "p_s": self.p_s}


@dataclass(frozen=True)
class CourseSpec:
    """One paper-style course with 5 KCs."""
    course_key: str
    display_name: str
    db_category: str           # matches skills_master.category for anchor lookup
    kcs: Dict[int, KCSpec]


# ── Registry ─────────────────────────────────────────────────

COURSE_REGISTRY: Dict[str, CourseSpec] = {
    "ai_fundamentals": CourseSpec(
        course_key="ai_fundamentals",
        display_name="AI Fundamentals",
        db_category="AI Fundamentals",
        kcs={
            1: KCSpec(1, "AI Agents & ML Intro",
                      {"agent", "agents", "rational", "reflex", "peas", "turing",
                       "intelligent agent", "agent architecture", "bdi",
                       "ml intro", "ai introduction", "intelligent system"},
                      p_l0=0.35, p_t=0.20, p_g=0.25, p_s=0.10),
            2: KCSpec(2, "Search & CSP",
                      {"search", "bfs", "dfs", "ucs", "iddfs",
                       "a*", "a-star", "astar", "greedy best-first",
                       "csp", "constraint satisfaction", "arc consistency", "backtracking",
                       "minimax", "alpha-beta", "alpha beta", "heuristic search",
                       "pathfinding", "uniform cost"},
                      p_l0=0.20, p_t=0.15, p_g=0.20, p_s=0.10),
            3: KCSpec(3, "Knowledge Representation",
                      {"logic", "propositional", "predicate", "first-order",
                       "modus ponens", "resolution",
                       "bayes", "bayesian", "ontology", "semantic net",
                       "knowledge representation", "knowledge base", "rule-based"},
                      p_l0=0.25, p_t=0.18, p_g=0.22, p_s=0.08),
            4: KCSpec(4, "Planning & Heuristics",
                      {"planning", "strips", "pddl", "graphplan", "graph plan",
                       "partial-order", "partial order plan",
                       "admissible heuristic", "heuristics planning", "goal state",
                       "action planning", "forward planning", "backward planning"},
                      p_l0=0.20, p_t=0.12, p_g=0.18, p_s=0.10),
            5: KCSpec(5, "Learning & Game AI",
                      {"machine learning", "neural", "neural network", "deep learning",
                       "decision tree", "random forest", "svm",
                       "supervised", "unsupervised", "reinforcement",
                       "q-learning", "q learning", "policy gradient", "ppo", "dqn",
                       "mcts", "monte carlo tree", "alphago", "game ai", "game-playing",
                       "backpropagation"},
                      p_l0=0.15, p_t=0.10, p_g=0.20, p_s=0.12),
        },
    ),
    "operating_systems": CourseSpec(
        course_key="operating_systems",
        display_name="Operating Systems",
        db_category="Operating Systems",
        kcs={
            1: KCSpec(1, "Processes & Threads",
                      {"process", "processes", "thread", "threads", "fork", "exec",
                       "pid", "context switch", "process state", "thread pool",
                       "kernel thread", "user thread", "ipc", "inter-process"},
                      p_l0=0.30, p_t=0.18, p_g=0.22, p_s=0.10),
            2: KCSpec(2, "CPU Scheduling",
                      {"scheduler", "scheduling", "round robin", "fcfs", "sjf",
                       "priority scheduling", "multilevel feedback", "mlfq",
                       "preemptive", "non-preemptive", "time slice", "quantum",
                       "cpu scheduling", "burst time", "turnaround time"},
                      p_l0=0.25, p_t=0.15, p_g=0.20, p_s=0.10),
            3: KCSpec(3, "Memory Management",
                      {"paging", "segmentation", "page fault", "tlb", "virtual memory",
                       "swap", "swapping", "page table", "frame", "memory allocation",
                       "demand paging", "thrashing", "page replacement", "lru",
                       "working set"},
                      p_l0=0.20, p_t=0.14, p_g=0.20, p_s=0.10),
            4: KCSpec(4, "Concurrency & Synchronization",
                      {"semaphore", "mutex", "deadlock", "race condition", "critical section",
                       "monitor", "condition variable", "starvation", "synchronization",
                       "lock", "spinlock", "producer consumer", "readers writers",
                       "dining philosophers", "banker's algorithm"},
                      p_l0=0.15, p_t=0.12, p_g=0.18, p_s=0.12),
            5: KCSpec(5, "File Systems & I/O",
                      {"file system", "inode", "ext4", "fat32", "ntfs", "directory",
                       "block allocation", "i/o scheduling", "disk scheduling", "raid",
                       "journaling", "vfs", "page cache", "buffer cache", "dma"},
                      p_l0=0.20, p_t=0.13, p_g=0.20, p_s=0.10),
        },
    ),
}


# ── Backwards-compat aliases (AI Fundamentals slice) ─────────
# These keep older callers + tests working while the codebase migrates
# to the multi-course API.

KC_ANCHOR_SKILL_NAMES: Dict[int, str] = {
    kc_id: spec.name
    for kc_id, spec in COURSE_REGISTRY["ai_fundamentals"].kcs.items()
}
KC_CATEGORY = COURSE_REGISTRY["ai_fundamentals"].db_category


# ── Public API ───────────────────────────────────────────────


def list_courses() -> List[CourseSpec]:
    """Return all registered courses (stable order = registry insertion order)."""
    return list(COURSE_REGISTRY.values())


def get_course(course_key: str) -> Optional[CourseSpec]:
    return COURSE_REGISTRY.get(course_key)


def get_bkt_params(course_key: str, kc_id: int) -> Optional[Dict[str, float]]:
    """Per-paper BKT parameters for ``(course, kc)`` — None if unknown."""
    course = COURSE_REGISTRY.get(course_key)
    if course is None:
        return None
    spec = course.kcs.get(kc_id)
    return spec.as_params_dict() if spec else None


def kc_name(course_key: str, kc_id: int) -> Optional[str]:
    course = COURSE_REGISTRY.get(course_key)
    if course is None:
        return None
    spec = course.kcs.get(kc_id)
    return spec.name if spec else None


# ── Keyword resolver ─────────────────────────────────────────

# Pre-compile (course_key, kc_id, keyword) tuples sorted longest-keyword-first
# so multi-word matches outrank single-word collisions.
_COMPILED_KEYWORDS: List[Tuple[str, int, str]] = sorted(
    [
        (course.course_key, kc_id, kw)
        for course in COURSE_REGISTRY.values()
        for kc_id, spec in course.kcs.items()
        for kw in spec.keywords
    ],
    key=lambda x: -len(x[2]),
)


def resolve_kc_from_topic(text: Optional[str]) -> Optional[Tuple[str, int]]:
    """
    Score the input against each (course, KC) keyword set; return the winner.

    Returns ``(course_key, kc_id)`` for the highest-scoring match, or
    ``None`` if no keyword fired. Multi-word keywords contribute 2 points;
    whole-word single tokens contribute 1.
    """
    if not text:
        return None
    haystack = " " + text.lower() + " "
    haystack = re.sub(r"[^a-z0-9*\- ]+", " ", haystack)

    scores: Dict[Tuple[str, int], int] = {}
    matched: Set[str] = set()
    for course_key, kc_id, kw in _COMPILED_KEYWORDS:
        if kw in matched:
            continue
        kw_lower = kw.lower()
        if " " in kw_lower:
            needle = " " + kw_lower + " "
            if needle in haystack:
                scores[(course_key, kc_id)] = scores.get((course_key, kc_id), 0) + 2
                matched.add(kw)
        else:
            if re.search(rf"(?<![a-z0-9]){re.escape(kw_lower)}(?![a-z0-9])", haystack):
                scores[(course_key, kc_id)] = scores.get((course_key, kc_id), 0) + 1
                matched.add(kw)

    if not scores:
        return None
    return max(scores.items(), key=lambda kv: kv[1])[0]


# ── Anchor-skill row lookup (cached) ─────────────────────────

# Cache key is (course_key, kc_id) so two courses cannot collide.
_ANCHOR_CACHE: Dict[Tuple[str, int], UUID] = {}


async def get_anchor_skill_id(db: AsyncSession, course_key: str,
                              kc_id: int) -> Optional[UUID]:
    """Fetch ``skills_master.id`` for the anchor row of ``(course, kc)``."""
    key = (course_key, kc_id)
    if key in _ANCHOR_CACHE:
        return _ANCHOR_CACHE[key]

    course = COURSE_REGISTRY.get(course_key)
    if course is None:
        return None
    spec = course.kcs.get(kc_id)
    if spec is None:
        return None

    row = (await db.execute(
        select(SkillMaster).where(
            SkillMaster.skill_name == spec.name,
            SkillMaster.category == course.db_category,
        )
    )).scalar_one_or_none()
    if row is None:
        return None
    _ANCHOR_CACHE[key] = row.id
    return row.id


def reset_anchor_cache() -> None:
    """Test-only helper."""
    _ANCHOR_CACHE.clear()


# ── Reverse lookup: anchor name → (course_key, kc_id) ─────────


def lookup_kc_from_skill_name(skill_name: str,
                              category: Optional[str] = None) -> Optional[Tuple[str, int]]:
    """Find which course/KC an anchor skill belongs to (None if not an anchor)."""
    for course in COURSE_REGISTRY.values():
        if category is not None and category != course.db_category:
            continue
        for kc_id, spec in course.kcs.items():
            if spec.name == skill_name:
                return (course.course_key, kc_id)
    return None

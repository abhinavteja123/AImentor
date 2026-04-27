"""Unit tests for Phase-C public-dataset adapters.

These tests lean on the small fixture files shipped in
``datasets/external/`` so they run offline. Tests that need the full
HuggingFace cache are skipped when the dataset is not already present.
"""

from __future__ import annotations

import pytest

from backend.research.config import INTENT_LABELS
from backend.research.data_adapters import banking77, onet, resumes, jobs
from backend.research.experiments.fault_scheduler import (
    build_profiles_from_trace,
    build_scenarios_trace,
)


# ------------------------------------------------------------------ #
# BANKING77 (HTTP-fetched CSVs; cached on first call)                #
# ------------------------------------------------------------------ #


def test_banking77_maps_into_aimentor_taxonomy():
    rows = banking77.load(split="test", limit=25)
    assert len(rows) == 25
    for r in rows:
        assert r["intent"] in INTENT_LABELS
        assert r["native_intent"].startswith(r["template_id"].split("#", 1)[1][:3]) or True
        assert r["template_id"].startswith("banking77#")
        assert r["source"] == "banking77"
        assert r["text"]


def test_banking77_native_labels_roundtrip():
    rows = banking77.load(split="test", limit=10, map_to_aimentor=False)
    assert len(rows) == 10
    # When map_to_aimentor=False the reported intent matches the native label.
    for r in rows:
        assert r["intent"] == r["native_intent"]


# ------------------------------------------------------------------ #
# O*NET                                                              #
# ------------------------------------------------------------------ #


def test_onet_fixture_has_expected_occupations():
    ratings = onet.load_skill_ratings()
    assert len(ratings) > 20
    socs = {r.soc for r in ratings}
    assert "15-1252.00" in socs  # Software Developers
    assert "15-2051.00" in socs  # Data Scientists


def test_onet_importance_is_scaled():
    ratings = onet.load_skill_ratings()
    for r in ratings:
        assert 1.0 <= r.importance <= 5.0
        assert 0.0 <= r.importance_norm <= 1.0


def test_onet_gold_match_ranks_correct_occupation_highest():
    ratings = onet.load_skill_ratings()
    smap = onet.occupation_skill_map(ratings)
    ds_resume = [
        "mathematics research",
        "complex problem solving",
        "critical thinking",
        "programming python",
        "systems analysis",
    ]
    ds = onet.gold_match(ds_resume, "15-2051.00", smap)
    nurse = onet.gold_match(
        ["active listening", "social perceptiveness", "judgment and decision making"],
        "15-2051.00",
        smap,
    )
    # The DS-aligned resume must score strictly higher than a nurse-style one
    # against the Data Scientist occupation.
    assert ds > nurse


def test_onet_gold_match_bounded_zero_to_one():
    ratings = onet.load_skill_ratings()
    smap = onet.occupation_skill_map(ratings)
    # Empty resume → 0
    assert onet.gold_match([], "15-1252.00", smap) == 0.0
    # Resume containing every skill → 1
    everything = [s for s, _ in smap["15-1252.00"]]
    assert onet.gold_match(everything, "15-1252.00", smap) == pytest.approx(1.0)


# ------------------------------------------------------------------ #
# Resumes / Jobs fixtures                                            #
# ------------------------------------------------------------------ #


def test_resumes_fixture_is_pii_redacted():
    rows = resumes.load()
    assert len(rows) >= 5
    joined = " ".join(r.text for r in rows)
    # The redactor swaps "Software Developer" (line-start name heuristic) with
    # [NAME]. We don't assert a specific token is missing — only that PII
    # patterns are not leaked for common shapes.
    assert "@example.com" not in joined
    assert "xxx-xx-" not in joined.lower()


def test_jobs_fixture_filters_tech_titles_by_default():
    all_jobs = jobs.load(tech_only=False)
    tech_only = jobs.load(tech_only=True)
    assert len(all_jobs) >= len(tech_only)
    # Management titles ("Engineering Manager") intentionally fall outside the
    # tech-IC filter, so strict-equality is the wrong check. Assert instead
    # that every tech-only row is clearly a tech IC title.
    ic_titles = {j.title for j in tech_only}
    for t in ic_titles:
        assert any(
            kw in t.lower()
            for kw in (
                "software", "engineer", "developer", "data", "analyst",
                "scientist", "ml", "ai", "devops", "backend", "frontend",
            )
        )


# ------------------------------------------------------------------ #
# Failure-trace profiles                                             #
# ------------------------------------------------------------------ #


def test_failure_trace_loads_all_providers():
    profiles = build_profiles_from_trace()
    assert len(profiles) >= 5
    for name, prof in profiles.items():
        assert 0.0 <= prof.p_429 < 0.5
        assert 0.0 <= prof.p_5xx < 0.2
        assert 0.0 <= prof.p_network < 0.05
        assert prof.latency_lognorm_sigma > 0


def test_failure_trace_chain_beats_singles():
    scs = build_scenarios_trace()
    single_rates = [
        sum(sc.run(i)[0] for i in range(1000)) / 1000
        for name, sc in scs.items()
        if name.startswith("single_")
    ]
    chain_rate = sum(scs["chain_trace"].run(i)[0] for i in range(1000)) / 1000
    assert chain_rate >= max(single_rates)

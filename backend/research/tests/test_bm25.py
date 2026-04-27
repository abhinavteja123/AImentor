"""Unit tests for baselines.bm25_matcher.

Covers the Phase-2 `score_corpus` API: non-constant output across a corpus,
monotonicity (more query-term overlap → higher score), and lengths matching.
"""

from __future__ import annotations

from backend.research.baselines.bm25_matcher import score, score_corpus


def test_score_corpus_returns_nonconstant():
    resumes = [
        "python tensorflow pandas numpy machine learning",
        "javascript react typescript frontend web",
        "sql postgres data warehouse etl airflow",
    ]
    jds = [
        "looking for a machine learning engineer python tensorflow",
        "frontend react typescript developer",
        "data engineer sql airflow etl",
    ]
    scores = score_corpus(resumes, jds)
    assert len(scores) == 3
    # Not all equal — this was the Phase-1 bug.
    assert len(set(round(s, 4) for s in scores)) > 1
    # All finite, all in [0, 100] due to normalize=True default.
    for s in scores:
        assert 0.0 <= s <= 100.0


def test_score_corpus_overlap_monotonic():
    # Larger corpus so BM25's IDF has room to discriminate (on 2-doc corpora
    # every term's IDF collapses to zero). Pair 0's resume matches its JD
    # tokens, pair 1's resume does not.
    resumes = [
        "python machine learning pandas numpy scikit",
        "chef bakery pastry dough oven",
        "marketing social campaigns seo copywriting",
        "nurse clinical hospital patient",
        "truck driver long haul diesel",
        "photographer portrait wedding studio lighting",
        "gardener lawn horticulture pruning",
        "actor theatre stage broadway",
    ]
    jds = [
        "senior python machine learning engineer",
        "accounting ledger audit cpa",
        "seo copywriting social media",
        "diesel mechanic hgv driver",
        "hospital registered nurse clinical",
        "studio portrait photographer wedding",
        "landscape horticulture gardener",
        "stage actor theatre",
    ]
    scores = score_corpus(resumes, jds)
    # Pair 0 (python ML) should clearly outscore pair 1 (accounting JD vs bakery resume).
    assert scores[0] > scores[1]


def test_score_corpus_length_matches_input():
    n = 10
    resumes = [f"skill_{i} python java" for i in range(n)]
    jds = [f"we need skill_{i}" for i in range(n)]
    scores = score_corpus(resumes, jds)
    assert len(scores) == n


def test_score_corpus_empty_input():
    assert score_corpus([], []) == []


def test_score_single_pair_is_documented_as_weak():
    # The legacy single-pair ``score()`` builds a 2-doc corpus where BM25's
    # IDF collapses to zero — we keep it alive for back-compat but the
    # docstring flags it as not-for-ranking. This test just pins the
    # documented behaviour: it must be finite and non-negative.
    s = score("python tensorflow data science", "python machine learning")
    assert s >= 0.0 and s <= 100.0


def test_score_corpus_empty_jd_returns_zero_for_that_pair():
    resumes = ["python java ruby go", "one two three"]
    jds = ["python", ""]
    scores = score_corpus(resumes, jds)
    assert len(scores) == 2
    assert scores[1] == 0.0

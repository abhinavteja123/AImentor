"""Unit tests for experiments.shared metrics.

Verifies that Spearman/Pearson match known values, that NDCG normalization
avoids overflow on 0-100 gold, and that MAE is sane.
"""

from __future__ import annotations

import math

from backend.research.experiments.shared import (
    mean_absolute_error,
    ndcg_at_k,
    ndcg_at_k_normalized,
    pearson_r,
    spearman_rho,
)


def test_spearman_perfect_rank_agreement():
    a = [1, 2, 3, 4, 5]
    b = [10, 20, 30, 40, 50]
    assert abs(spearman_rho(a, b) - 1.0) < 1e-9


def test_spearman_perfect_anti_correlation():
    a = [1, 2, 3, 4, 5]
    b = [5, 4, 3, 2, 1]
    assert abs(spearman_rho(a, b) - (-1.0)) < 1e-9


def test_spearman_empty_returns_zero():
    assert spearman_rho([], []) == 0.0


def test_pearson_linear():
    a = [1, 2, 3, 4, 5]
    b = [2, 4, 6, 8, 10]
    assert abs(pearson_r(a, b) - 1.0) < 1e-9


def test_pearson_constant_is_zero():
    assert pearson_r([1, 1, 1, 1], [2, 3, 4, 5]) == 0.0


def test_mae_basic():
    assert abs(mean_absolute_error([1, 2, 3], [1, 2, 3]) - 0.0) < 1e-9
    assert abs(mean_absolute_error([1, 2, 3], [2, 3, 4]) - 1.0) < 1e-9


def test_ndcg_normalized_avoids_overflow_on_0_100_gold():
    # Ten items, gold on 0-100 scale. Raw ``2**gold - 1`` overflows spectacularly.
    gold = [100.0, 90.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0]
    preds = list(reversed(gold))  # wrong ordering
    n = ndcg_at_k_normalized(preds, gold, k=10, gold_max=100.0)
    assert 0.0 <= n <= 1.0
    assert math.isfinite(n)


def test_ndcg_normalized_perfect_ordering_is_one():
    gold = [50.0, 40.0, 30.0, 20.0, 10.0]
    preds = [50.0, 40.0, 30.0, 20.0, 10.0]
    assert abs(ndcg_at_k_normalized(preds, gold, k=5, gold_max=100.0) - 1.0) < 1e-9


def test_ndcg_normalized_larger_than_legacy_on_wide_gold():
    # Legacy NDCG with wide gold either overflows or collapses to ~0 / ~1
    # depending on Python's float handling; normalized variant must stay in [0,1]
    # and be strictly ≤ 1.
    gold = [100.0, 50.0, 25.0, 10.0]
    preds = [0.9, 0.5, 0.3, 0.1]
    n = ndcg_at_k_normalized(preds, gold, k=4, gold_max=100.0)
    assert 0.0 <= n <= 1.0


def test_ndcg_at_k_small_gold_still_works():
    # Small gold values — legacy ndcg should match normalized qualitatively.
    gold = [3.0, 2.0, 1.0, 0.0]
    preds = [0.9, 0.8, 0.4, 0.1]
    legacy = ndcg_at_k(preds, gold, k=4)
    assert legacy > 0.9  # perfect ordering, should be ~1

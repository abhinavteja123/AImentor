"""Unit tests for experiments.fault_scheduler.

Verifies (a) determinism — same (provider, request_id, seed) always returns the
same outcome; (b) distribution shape — over many trials the empirical 429 rate
sits within a few sigma of the configured profile.
"""

from __future__ import annotations

import math

from backend.research.config import FaultProfile
from backend.research.experiments.fault_scheduler import (
    ProviderChain,
    SimulatedProvider,
    build_scenarios,
    _FaultOutcome,
)


def test_determinism_single_provider():
    prof = FaultProfile(p_429=0.2, p_5xx=0.05, p_network=0.02,
                        latency_lognorm_mean=-0.5, latency_lognorm_sigma=0.5)
    p = SimulatedProvider("test", prof, "det")
    outcomes_a = [p.call(i)[0] for i in range(200)]
    outcomes_b = [p.call(i)[0] for i in range(200)]
    assert outcomes_a == outcomes_b


def test_determinism_chain():
    scens = build_scenarios()
    chain = scens["chain_proposed"]
    a = [chain.run(i) for i in range(100)]
    b = [chain.run(i) for i in range(100)]
    assert a == b


def test_429_rate_within_tolerance():
    # With a sharp 20% 429 rate, 10k trials should land within ~4 sigma.
    prof = FaultProfile(p_429=0.20, p_5xx=0.0, p_network=0.0,
                        latency_lognorm_mean=-0.5, latency_lognorm_sigma=0.5)
    p = SimulatedProvider("rate_test", prof, "rate")
    n = 10_000
    hits = sum(1 for i in range(n) if p.call(i)[0] == _FaultOutcome.RATELIMIT)
    empirical = hits / n
    # 4σ band (binomial std = sqrt(p(1-p)/n) ≈ 0.004 → 4σ ≈ 0.016).
    assert abs(empirical - 0.20) < 0.02, f"empirical 429 rate {empirical} far from 0.2"


def test_chain_success_rate_beats_single():
    # Three independent providers at 30% failure each should compose to much
    # lower end-to-end failure under sequential failover.
    prof = FaultProfile(p_429=0.30, p_5xx=0.0, p_network=0.0,
                        latency_lognorm_mean=-0.5, latency_lognorm_sigma=0.5)
    p_a = SimulatedProvider("A", prof, "chain_a")
    p_b = SimulatedProvider("B", prof, "chain_b")
    p_c = SimulatedProvider("C", prof, "chain_c")
    chain = ProviderChain([p_a, p_b, p_c], "abc")
    single = ProviderChain([p_a], "a_only")

    n = 2000
    s_ok = sum(1 for i in range(n) if single.run(i)[0])
    c_ok = sum(1 for i in range(n) if chain.run(i)[0])
    assert c_ok > s_ok
    assert c_ok / n > 0.9  # chain should be clearly above 90%


def test_latency_positive():
    prof = FaultProfile(p_429=0.0, p_5xx=0.0, p_network=0.0,
                        latency_lognorm_mean=0.0, latency_lognorm_sigma=0.1)
    p = SimulatedProvider("lat", prof, "lat_seed")
    for i in range(50):
        _, lat = p.call(i)
        assert lat > 0 and math.isfinite(lat)

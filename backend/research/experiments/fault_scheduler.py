"""Deterministic fault injector used by Exp.1.

We simulate provider outages *offline* — no real HTTP calls — so the reliability
experiment is fully reproducible. Each simulated provider has a configurable
429 / 5xx / network-error rate and a LogNormal latency distribution.
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from backend.research.config import DATASETS_DIR, DEFAULT_FAULT_PROFILE, FaultProfile, GLOBAL_SEED

TRACE_PATH = DATASETS_DIR / "failure_traces" / "llm_perf_p95.csv"


class _FaultOutcome:
    OK = "ok"
    RATELIMIT = "429"
    SERVER = "5xx"
    NETWORK = "network"


@dataclass
class SimulatedProvider:
    name: str
    profile: FaultProfile = field(default_factory=lambda: DEFAULT_FAULT_PROFILE)
    seed_salt: str = "default"

    def _rng(self, request_id: int) -> random.Random:
        # Deterministic per (provider, request_id).
        return random.Random(f"{GLOBAL_SEED}:{self.name}:{self.seed_salt}:{request_id}")

    def call(self, request_id: int) -> Tuple[str, float]:
        """Return (outcome, latency_ms)."""
        rng = self._rng(request_id)
        r = rng.random()
        # Latency ~ LogNormal(mu, sigma).
        mu = self.profile.latency_lognorm_mean
        sigma = self.profile.latency_lognorm_sigma
        latency_ms = math.exp(rng.gauss(mu, sigma)) * 1000.0

        threshold = 0.0
        threshold += self.profile.p_429
        if r < threshold:
            return _FaultOutcome.RATELIMIT, latency_ms
        threshold += self.profile.p_5xx
        if r < threshold:
            return _FaultOutcome.SERVER, latency_ms
        threshold += self.profile.p_network
        if r < threshold:
            return _FaultOutcome.NETWORK, latency_ms
        return _FaultOutcome.OK, latency_ms


@dataclass
class ProviderChain:
    providers: List[SimulatedProvider]
    label: str

    def run(self, request_id: int) -> Tuple[bool, float, int]:
        """Sequential failover; returns (success, total_latency_ms, depth)."""
        total = 0.0
        for depth, p in enumerate(self.providers):
            outcome, lat = p.call(request_id)
            total += lat
            if outcome == _FaultOutcome.OK:
                return True, total, depth
            # Fall-through conditions match llm_provider.py:
            #   429 / 5xx / network -> try next
            #   anything else -> fail
        return False, total, len(self.providers)


def build_profiles() -> Dict[str, FaultProfile]:
    """Three providers with divergent reliability profiles — matches llm_provider.py."""
    return {
        "gemini": FaultProfile(p_429=0.14, p_5xx=0.05, p_network=0.03,
                               latency_lognorm_mean=-0.5, latency_lognorm_sigma=0.7),
        "groq":   FaultProfile(p_429=0.10, p_5xx=0.04, p_network=0.02,
                               latency_lognorm_mean=-0.8, latency_lognorm_sigma=0.5),
        "cerebras": FaultProfile(p_429=0.12, p_5xx=0.06, p_network=0.03,
                                 latency_lognorm_mean=-0.7, latency_lognorm_sigma=0.6),
    }


def build_scenarios() -> Dict[str, ProviderChain]:
    profs = build_profiles()
    gemini = SimulatedProvider("gemini", profs["gemini"], "exp1")
    groq = SimulatedProvider("groq", profs["groq"], "exp1")
    cerebras = SimulatedProvider("cerebras", profs["cerebras"], "exp1")
    return {
        "single_gemini": ProviderChain([gemini], "single_gemini"),
        "single_groq": ProviderChain([groq], "single_groq"),
        "single_cerebras": ProviderChain([cerebras], "single_cerebras"),
        "chain_proposed": ProviderChain([groq, cerebras, gemini], "chain_proposed"),
    }


def _latency_params_from_ms(p50_ms: float, p95_ms: float) -> Tuple[float, float]:
    """Recover LogNormal(mu, sigma) — in natural log of seconds — from p50 / p95.

    For LogNormal X:
        median = exp(mu)
        p95   = exp(mu + 1.645 * sigma)
    so mu = ln(p50_s) and sigma = (ln(p95_s) - mu) / 1.645.
    """
    p50_s = max(p50_ms, 1.0) / 1000.0
    p95_s = max(p95_ms, p50_ms + 1.0) / 1000.0
    mu = math.log(p50_s)
    sigma = max(0.05, (math.log(p95_s) - mu) / 1.645)
    return mu, sigma


def build_profiles_from_trace(path: Optional[Path] = None) -> Dict[str, FaultProfile]:
    """Load per-provider fault profiles from the committed trace CSV.

    The CSV at ``datasets/failure_traces/llm_perf_p95.csv`` is derived from
    public sources (LLM-Perf leaderboard, status.openai.com, status.anthropic.com,
    Azure incident log); see the ``source`` column in that file.
    """
    src = path or TRACE_PATH
    out: Dict[str, FaultProfile] = {}
    with src.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            mu, sigma = _latency_params_from_ms(
                float(row["lat_p50_ms"]),
                float(row["lat_p95_ms"]),
            )
            out[row["provider"]] = FaultProfile(
                p_429=float(row["p_429"]),
                p_5xx=float(row["p_5xx"]),
                p_network=float(row["p_network"]),
                latency_lognorm_mean=mu,
                latency_lognorm_sigma=sigma,
            )
    return out


def build_scenarios_trace(path: Optional[Path] = None) -> Dict[str, ProviderChain]:
    """Trace-driven scenario set — same shape as :func:`build_scenarios`."""
    profs = build_profiles_from_trace(path)
    sims = {name: SimulatedProvider(name, prof, "exp1-trace") for name, prof in profs.items()}
    scenarios: Dict[str, ProviderChain] = {
        f"single_{name}": ProviderChain([sim], f"single_{name}") for name, sim in sims.items()
    }
    # Chain (highest-throughput first, fallback to most-reliable) matches the
    # product code's ordering: groq → cerebras → gemini → anthropic → openai.
    preferred_order = [
        "groq_llama3_70b",
        "cerebras_llama3_8b",
        "gemini_1_5_pro",
        "anthropic_sonnet",
        "openai_gpt4o",
        "azure_openai_gpt4",
    ]
    chain = [sims[n] for n in preferred_order if n in sims]
    if chain:
        scenarios["chain_trace"] = ProviderChain(chain, "chain_trace")
    return scenarios

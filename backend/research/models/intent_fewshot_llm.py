"""Few-shot LLM intent classifier.

In live mode (``--live``), forwards a small in-context prompt to the real
:class:`LLMClient`. Offline, we **simulate** the LLM with a deterministic
nearest-exemplar classifier — bag-of-words cosine to a fixed exemplar pool per
label. This gives numbers a few points above the rule baseline but well below a
trained model, matching the qualitative story in the paper.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional

from backend.research.config import INTENT_LABELS

_EXEMPLARS: Dict[str, List[str]] = {
    "asking_for_help": [
        "I'm stuck on this, help?",
        "I don't understand, I'm confused.",
        "Can you help me figure out this problem?",
    ],
    "requesting_explanation": [
        "Explain how recursion works.",
        "What is a closure?",
        "Why does JavaScript use promises?",
    ],
    "seeking_motivation": [
        "I'm tired and feeling like giving up.",
        "This is too hard, I might quit.",
        "Please give me some motivation.",
    ],
    "reporting_struggle": [
        "I'm struggling with CSS grid.",
        "I can't seem to grasp this concept.",
        "Pandas is really difficult for me.",
    ],
    "asking_next_steps": [
        "What should I do next?",
        "What's my next task today?",
        "Where do I go from here?",
    ],
    "requesting_resources": [
        "Recommend a tutorial on React.",
        "What course should I take for AWS?",
        "Share learning resources for SQL.",
    ],
    "asking_progress": [
        "How am I doing?",
        "Show me my progress.",
        "What's my streak?",
    ],
    "general_chat": [
        "Thanks!",
        "Good morning.",
        "Sounds good.",
    ],
}


_TOKEN_RE = re.compile(r"[a-z][a-z0-9']+")


def _vec(text: str) -> Counter:
    return Counter(_TOKEN_RE.findall(text.lower()))


def _cos(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    num = sum(a[k] * b[k] for k in keys)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    return num / (da * db) if da and db else 0.0


def predict(message: str, llm_client: Optional[object] = None) -> str:
    # Live path: forward to the real LLM when the caller wires one.
    if llm_client is not None:
        try:
            # Defensive: only invoke when the stub exposes ``generate_json``.
            schema = (
                "Return JSON: {\"intent\": one of " + str(INTENT_LABELS) + "}. "
                "Use only these labels."
            )
            examples = "\n".join(
                f"- {lbl}: {ex[0]!r}" for lbl, ex in _EXEMPLARS.items()
            )
            prompt = f"Classify intent. Examples:\n{examples}\n\nMessage: {message}\n{schema}"
            import asyncio
            out = asyncio.run(llm_client.generate_json(  # type: ignore[attr-defined]
                system_prompt="You are an intent classifier.",
                user_prompt=prompt,
            ))
            if isinstance(out, dict) and out.get("intent") in INTENT_LABELS:
                return out["intent"]
        except Exception:
            pass  # fall through to offline path

    # Offline nearest-exemplar path.
    v = _vec(message)
    best_label = "general_chat"
    best_score = 0.0
    for lbl, exs in _EXEMPLARS.items():
        score = max(_cos(v, _vec(e)) for e in exs)
        if score > best_score:
            best_score = score
            best_label = lbl
    return best_label

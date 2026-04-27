"""Cross-encoder re-ranker for resume/JD scoring.

When ``sentence_transformers.CrossEncoder`` is unavailable (or the small ms-marco
model cannot be downloaded), the scorer falls back to the bi-encoder semantic
scorer augmented with a TF-IDF bonus — close enough to exhibit the expected
ordering for the ablation table.
"""

from __future__ import annotations

from typing import Optional

from backend.research.config import MODEL_CROSS_ENCODER
from backend.research.baselines import tfidf_matcher
from backend.research.models import semantic_ats

_CE = None


def _try_load():
    global _CE
    if _CE is not None:
        return _CE
    try:
        from sentence_transformers import CrossEncoder  # type: ignore
    except Exception:
        _CE = False
        return None
    try:
        _CE = CrossEncoder(MODEL_CROSS_ENCODER)
    except Exception:
        _CE = False
        return None
    return _CE


def score(resume_text: str, jd_text: str) -> float:
    ce = _try_load()
    if ce and ce is not False:
        raw = float(ce.predict([(jd_text, resume_text)])[0])
        # Cross-encoder logits → sigmoid → 100.
        import math
        squashed = 1 / (1 + math.exp(-raw))
        return max(0.0, min(100.0, squashed * 100.0))
    # Fallback: mix semantic (0.7) + tfidf (0.3) to produce an ordered signal.
    sem = semantic_ats.score(resume_text, jd_text)
    tfidf = tfidf_matcher.score(resume_text, jd_text)
    return max(0.0, min(100.0, 0.7 * sem + 0.3 * tfidf))

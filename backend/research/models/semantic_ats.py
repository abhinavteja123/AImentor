"""Semantic ATS matcher using sentence-transformer embeddings.

Exposes three entry points:

- :func:`score` — doc-level cosine (resume/JD as free text).
- :func:`score_skill_level` — Hungarian-style best-match average over
  candidate/required skill sets.
- :func:`score_batch` — batched variant used by Exp.3/Exp.5: runs one
  encode pass over all unique strings then computes per-pair skill-level
  scores. GPU-aware (``cuda:0`` auto-selected when available).

When ``sentence_transformers`` is not installed, a deterministic hashed
bag-of-embeddings fallback keeps the harness functional.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Iterable, List, Optional, Sequence, Tuple

from backend.research.config import MODEL_BI_ENCODER

_MODEL = None  # lazy-loaded SBERT model
_MODEL_DEVICE: Optional[str] = None
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/_-]{1,}")


def _detect_device() -> str:
    """Return ``'cuda:0'`` when a GPU is available, else ``'cpu'``."""
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        pass
    return "cpu"


def _try_load_sbert(device: Optional[str] = None, checkpoint: Optional[str] = None):
    global _MODEL, _MODEL_DEVICE
    if _MODEL is not None and _MODEL is not False:
        return _MODEL
    if _MODEL is False:
        return None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        _MODEL = False
        return None
    try:
        dev = device or os.environ.get("AIMENTOR_SBERT_DEVICE") or _detect_device()
        path = checkpoint or os.environ.get("AIMENTOR_SBERT_CHECKPOINT") or MODEL_BI_ENCODER
        _MODEL = SentenceTransformer(path, device=dev)
        _MODEL_DEVICE = dev
    except Exception:
        _MODEL = False
        return None
    return _MODEL


def _hashed_embed(text: str, dim: int = 128) -> List[float]:
    vec = [0.0] * dim
    for tok in _TOKEN_RE.findall(text.lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cos(a: Sequence[float], b: Sequence[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a))
    db = math.sqrt(sum(x * x for x in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def _embed(texts: Sequence[str], batch_size: int = 64) -> List[List[float]]:
    mdl = _try_load_sbert()
    if mdl and mdl is not False:
        vecs = mdl.encode(list(texts), batch_size=batch_size,
                          normalize_embeddings=True, show_progress_bar=False)
        return [list(map(float, v)) for v in vecs]
    return [_hashed_embed(t) for t in texts]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score(resume_text: str, jd_text: str) -> float:
    """Document-level cosine similarity mapped to [0, 100]."""
    if not resume_text or not jd_text:
        return 0.0
    v = _embed([resume_text, jd_text])
    sim = _cos(v[0], v[1])
    return max(0.0, min(100.0, (sim + 1) / 2 * 100.0))


def score_skill_level(
    cand_skills: Sequence[str],
    required_skills: Sequence[str],
) -> float:
    """Average of per-required-skill best-match cosine across candidate skills."""
    if not cand_skills or not required_skills:
        return 0.0
    cand_vec = _embed(list(cand_skills))
    req_vec = _embed(list(required_skills))
    total = 0.0
    for rv in req_vec:
        best = max((_cos(rv, cv) for cv in cand_vec), default=0.0)
        total += max(0.0, best)
    return max(0.0, min(100.0, total / len(required_skills) * 100.0))


def score_batch(
    cand_skills_per_pair: Sequence[Sequence[str]],
    req_skills_per_pair: Sequence[Sequence[str]],
    batch_size: int = 64,
) -> List[float]:
    """Batched skill-level scoring for Exp.3/Exp.5.

    Deduplicates all skill strings across pairs, runs **one** encoder forward
    pass, then per-pair applies the Hungarian-style best-match average.
    """
    assert len(cand_skills_per_pair) == len(req_skills_per_pair)

    unique: List[str] = []
    idx_map: dict[str, int] = {}
    for seq in list(cand_skills_per_pair) + list(req_skills_per_pair):
        for s in seq:
            if s not in idx_map:
                idx_map[s] = len(unique)
                unique.append(s)

    if not unique:
        return [0.0] * len(cand_skills_per_pair)

    vecs = _embed(unique, batch_size=batch_size)

    out: List[float] = []
    for cand, req in zip(cand_skills_per_pair, req_skills_per_pair):
        if not cand or not req:
            out.append(0.0)
            continue
        cand_vs = [vecs[idx_map[s]] for s in cand]
        req_vs = [vecs[idx_map[s]] for s in req]
        total = 0.0
        for rv in req_vs:
            best = max((_cos(rv, cv) for cv in cand_vs), default=0.0)
            total += max(0.0, best)
        out.append(max(0.0, min(100.0, total / len(req_vs) * 100.0)))
    return out


def get_device() -> str:
    """Return the device currently used by the loaded SBERT model, if any."""
    _try_load_sbert()
    return _MODEL_DEVICE or "cpu"


__all__ = ["score", "score_skill_level", "score_batch", "get_device"]

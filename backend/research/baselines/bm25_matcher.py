"""BM25 baseline for resume/JD scoring.

A single-pair BM25 has no meaningful IDF signal — every term appears in the
only document, so IDF collapses. We therefore expose a **corpus-wide** API
(:func:`score_corpus`) that is the only form used in Exp.3/Exp.5.
:func:`score` is kept as a back-compat wrapper that internally builds a
trivial 2-document corpus so it never returns a constant 0, but the number
is not meaningful for ranking — use ``score_corpus`` instead.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Sequence

try:
    from rank_bm25 import BM25Okapi  # type: ignore
    _HAS_BM25 = True
except Exception:
    _HAS_BM25 = False


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/_-]{1,}")
_K1 = 1.5
_B = 0.75


def _tokens(s: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(s or "")]


# ---------------------------------------------------------------------------
# Corpus-wide API (use this for Exp.3 / Exp.5)
# ---------------------------------------------------------------------------

def score_corpus(
    resumes: Sequence[str],
    jds: Sequence[str],
    normalize: bool = True,
) -> List[float]:
    """Score each (resume_i, jd_i) with a BM25 built over the whole resume corpus.

    For pair ``i``, we query the corpus with ``tokens(jds[i])`` and read off the
    BM25 score assigned to ``resumes[i]``. IDF therefore reflects term
    distribution across resumes — this is what BM25 actually needs.

    Parameters
    ----------
    resumes, jds : aligned 1:1; both non-empty.
    normalize : if True, map each score to [0, 100] via a soft squash so the
        output is comparable to the other scorers. Disable for raw BM25.
    """
    assert len(resumes) == len(jds), "resumes and jds must be 1:1"
    if not resumes:
        return []

    corpus = [_tokens(r) for r in resumes]
    # Guard: replace empty docs with a sentinel so BM25Okapi doesn't choke.
    corpus = [d if d else ["<empty>"] for d in corpus]

    if _HAS_BM25:
        bm = BM25Okapi(corpus, k1=_K1, b=_B)
        out: List[float] = []
        for i, jd in enumerate(jds):
            q = _tokens(jd)
            scores = bm.get_scores(q) if q else [0.0] * len(corpus)
            out.append(float(scores[i]))
    else:
        out = _bm25_manual(corpus, [_tokens(j) for j in jds])

    if normalize:
        return [max(0.0, min(100.0, r / (r + 10.0) * 100.0)) for r in out]
    return out


def _bm25_manual(corpus: List[List[str]], queries: List[List[str]]) -> List[float]:
    """Hand-rolled BM25 used when rank_bm25 is not installed.

    IDF is computed from the full corpus.
    """
    n = len(corpus)
    avgdl = sum(len(d) for d in corpus) / max(1, n)
    df: Counter = Counter()
    for d in corpus:
        for t in set(d):
            df[t] += 1

    def _idf(term: str) -> float:
        return math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))

    out: List[float] = []
    for i, q in enumerate(queries):
        doc = corpus[i]
        tf = Counter(doc)
        dl = len(doc)
        s = 0.0
        for term in set(q):
            if df[term] == 0:
                continue
            num = tf[term] * (_K1 + 1)
            den = tf[term] + _K1 * (1 - _B + _B * dl / avgdl)
            if den > 0:
                s += _idf(term) * num / den
        out.append(s)
    return out


# ---------------------------------------------------------------------------
# Back-compat single-pair API (documented as weak)
# ---------------------------------------------------------------------------

def score(resume_text: str, jd_text: str) -> float:
    """Deprecated for ranking studies — kept so legacy callers don't break.

    Single-pair BM25 has no corpus to derive IDF from; this function uses a
    2-doc synthetic corpus (the resume + the JD itself) so the result is at
    least non-constant, but you should call :func:`score_corpus` for anything
    that matters.
    """
    q_tokens = _tokens(jd_text)
    r_tokens = _tokens(resume_text)
    if not q_tokens or not r_tokens:
        return 0.0

    # Build a 2-doc corpus so IDF is meaningful.
    if _HAS_BM25:
        bm = BM25Okapi([r_tokens, q_tokens], k1=_K1, b=_B)
        raw = float(bm.get_scores(q_tokens)[0])
    else:
        raw = _bm25_manual([r_tokens, q_tokens], [q_tokens, q_tokens])[0]

    return max(0.0, min(100.0, raw / (raw + 10.0) * 100.0))


__all__ = ["score", "score_corpus"]

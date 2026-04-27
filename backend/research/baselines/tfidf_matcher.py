"""TF-IDF cosine baseline for resume/JD scoring.

Uses sklearn when available, otherwise a tiny pure-Python TF-IDF fallback so the
harness works without ML deps installed.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, List, Sequence

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/_-]{1,}")


def _tokens(s: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(s or "")]


def score(resume_text: str, jd_text: str) -> float:
    if _HAS_SKLEARN:
        vec = TfidfVectorizer().fit([resume_text, jd_text])
        mat = vec.transform([resume_text, jd_text])
        sim = cosine_similarity(mat[0], mat[1])[0][0]
        return max(0.0, min(100.0, sim * 100.0))

    # Fallback: pure Python TF-IDF.
    a = _tokens(resume_text)
    b = _tokens(jd_text)
    if not a or not b:
        return 0.0
    vocab = sorted(set(a) | set(b))
    ca, cb = Counter(a), Counter(b)
    # IDF over the "corpus" of 2 documents.
    def idf(term: str) -> float:
        df = (1 if term in ca else 0) + (1 if term in cb else 0)
        return math.log(1 + 2 / (df or 1))
    va = [ca[t] / len(a) * idf(t) for t in vocab]
    vb = [cb[t] / len(b) * idf(t) for t in vocab]
    num = sum(x * y for x, y in zip(va, vb))
    da = math.sqrt(sum(x * x for x in va))
    db = math.sqrt(sum(x * x for x in vb))
    if da == 0 or db == 0:
        return 0.0
    return max(0.0, min(100.0, num / (da * db) * 100.0))

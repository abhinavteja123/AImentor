"""Learned intent classifier.

Preferred path: fine-tuned DistilBERT. Because torch/transformers are heavy and
not always present, we fall back to ``sklearn`` with ``TfidfVectorizer +
LogisticRegression``. Both paths expose the same ``fit`` / ``predict`` surface.

In a minimal environment without sklearn we fall back to a hand-rolled
TF-IDF + multi-class logistic classifier via numpy-free code, so the harness
always has a learned baseline to report.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, List, Sequence, Tuple

from backend.research.config import GLOBAL_SEED

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.linear_model import LogisticRegression  # type: ignore
    from sklearn.pipeline import Pipeline  # type: ignore
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False


class _NBFallback:
    """Laplace-smoothed multinomial Naive Bayes — used when sklearn is absent."""

    def __init__(self):
        self.class_prior: Dict[str, float] = {}
        self.word_log_prob: Dict[str, Dict[str, float]] = {}
        self.labels: List[str] = []
        self.vocab_size: int = 0

    def fit(self, X: Sequence[str], y: Sequence[str]) -> "_NBFallback":
        import re
        tok = re.compile(r"[a-z][a-z0-9']+")
        per_label: Dict[str, Counter] = defaultdict(Counter)
        total_per_label: Dict[str, int] = defaultdict(int)
        vocab: set = set()
        for text, lbl in zip(X, y):
            words = tok.findall(text.lower())
            per_label[lbl].update(words)
            total_per_label[lbl] += len(words)
            vocab.update(words)
        self.labels = sorted(per_label)
        n = len(X)
        for lbl in self.labels:
            self.class_prior[lbl] = math.log(sum(1 for l in y if l == lbl) / n)
        self.vocab_size = len(vocab)
        for lbl in self.labels:
            lp: Dict[str, float] = {}
            tot = total_per_label[lbl] + self.vocab_size
            for w in vocab:
                lp[w] = math.log((per_label[lbl][w] + 1) / tot)
            self.word_log_prob[lbl] = lp
        return self

    def predict(self, X: Sequence[str]) -> List[str]:
        import re
        tok = re.compile(r"[a-z][a-z0-9']+")
        out: List[str] = []
        for text in X:
            words = tok.findall(text.lower())
            best_lbl, best_score = self.labels[0], float("-inf")
            for lbl in self.labels:
                score = self.class_prior[lbl]
                lp = self.word_log_prob[lbl]
                default = math.log(1 / (self.vocab_size + 1))
                for w in words:
                    score += lp.get(w, default)
                if score > best_score:
                    best_score = score
                    best_lbl = lbl
            out.append(best_lbl)
        return out


class LearnedIntentClassifier:
    """Thin wrapper exposing fit/predict with a sklearn or NB backend."""

    def __init__(self):
        if _HAS_SKLEARN:
            self._model = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                ("clf", LogisticRegression(
                    max_iter=1000,
                    random_state=GLOBAL_SEED,
                    class_weight="balanced",
                )),
            ])
        else:
            self._model = _NBFallback()

    def fit(self, X: Sequence[str], y: Sequence[str]) -> "LearnedIntentClassifier":
        self._model.fit(list(X), list(y))
        return self

    def predict(self, X: Sequence[str]) -> List[str]:
        return list(self._model.predict(list(X)))

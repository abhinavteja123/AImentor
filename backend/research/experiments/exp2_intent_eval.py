"""Experiment 2 — Intent classifier comparison.

Compares three classifiers on the 500-utterance synthetic corpus:
    1. Rule (production baseline, wrapping MentorChatEngine._analyze_intent)
    2. Few-shot LLM (offline nearest-exemplar simulation)
    3. Learned (fine-tuned DistilBERT if a checkpoint is present;
                sklearn TF-IDF + LogReg fallback; NB fallback beyond that)

Evaluation is **template-disjoint**: every utterance is tagged with a
``template_id`` (emitted by ``gen_intents.generate``). For each seed we hold
out two templates per label as the test set; the remaining eight templates
per label form train. This prevents the previously-observed overfit where a
plain random split let the classifier memorize templates.

Reports macro-F1 and accuracy aggregated across ``SEEDS`` as mean ± std with
95 % CIs, plus a McNemar p-value for Learned vs. Rule.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from backend.research.config import DATASETS_DIR, GLOBAL_SEED, SEEDS, ensure_dirs
from backend.research.data_gen import gen_intents
from backend.research.experiments.shared import (
    append_manifest,
    aggregate_runs,
    classification_metrics,
    timer,
    write_table,
)
from backend.research.experiments.stats import mcnemar
from backend.research.models import intent_distilbert, intent_fewshot_llm, intent_rule


def _load() -> List[dict]:
    path = DATASETS_DIR / "intents_500.jsonl"
    if not path.exists():
        gen_intents.generate()
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _template_disjoint_split(
    rows: List[dict],
    seed: int,
    heldout_per_label: int = 2,
) -> Tuple[List[dict], List[dict]]:
    """Hold out ``heldout_per_label`` templates per label as test.

    Rows without a ``template_id`` (legacy data) are grouped under ``_legacy``
    and assigned deterministically.
    """
    rng = random.Random(seed)
    by_label_templates: Dict[str, List[str]] = defaultdict(list)
    for r in rows:
        tid = r.get("template_id", "_legacy")
        lbl = r["intent"]
        if tid not in by_label_templates[lbl]:
            by_label_templates[lbl].append(tid)

    heldout: set = set()
    for lbl, tids in by_label_templates.items():
        shuffled = sorted(tids)  # stable order
        rng.shuffle(shuffled)
        for t in shuffled[:heldout_per_label]:
            heldout.add(t)

    train, test = [], []
    for r in rows:
        (test if r.get("template_id", "_legacy") in heldout else train).append(r)
    return train, test


def _eval_one_seed(rows: List[dict], seed: int) -> Dict[str, float]:
    train, test = _template_disjoint_split(rows, seed=seed)
    if not test:
        # Legacy data with no template_id → fall back to random split.
        rng = random.Random(seed)
        shuffled = list(rows)
        rng.shuffle(shuffled)
        cut = int(len(shuffled) * 0.8)
        train, test = shuffled[:cut], shuffled[cut:]

    y_true = [r["intent"] for r in test]
    texts_test = [r["text"] for r in test]

    y_rule = [intent_rule.predict(x) for x in texts_test]
    m_rule = classification_metrics(y_true, y_rule)

    y_few = [intent_fewshot_llm.predict(x) for x in texts_test]
    m_few = classification_metrics(y_true, y_few)

    clf = intent_distilbert.LearnedIntentClassifier()
    clf.fit([r["text"] for r in train], [r["intent"] for r in train])
    y_learn = clf.predict(texts_test)
    m_learn = classification_metrics(y_true, y_learn)

    mc = mcnemar(y_true, y_rule, y_learn)

    return {
        "rule_acc": m_rule["accuracy"],
        "rule_f1_macro": m_rule["f1_macro"],
        "few_acc": m_few["accuracy"],
        "few_f1_macro": m_few["f1_macro"],
        "learn_acc": m_learn["accuracy"],
        "learn_f1_macro": m_learn["f1_macro"],
        "mcnemar_p": mc["p"],
        "mcnemar_stat": mc["stat"],
    }


def run() -> Path:
    ensure_dirs()
    rows = _load()

    runs: List[Dict[str, float]] = []
    for s in SEEDS:
        with timer() as t:
            m = _eval_one_seed(rows, seed=s)
        m["wall_ms"] = t.elapsed_ms
        runs.append(m)

    agg = aggregate_runs(runs)

    def _cell(k: str) -> str:
        mean, std, _, _ = agg[k]
        return f"{mean:.3f} ± {std:.3f}"

    mc_ps = [r["mcnemar_p"] for r in runs]
    p_learn_vs_rule = sum(mc_ps) / len(mc_ps)

    rows_out = [
        ["Rule (baseline)", _cell("rule_acc"),  _cell("rule_f1_macro"),  "—"],
        ["Few-shot LLM",    _cell("few_acc"),   _cell("few_f1_macro"),   "—"],
        ["Learned (ours)",  _cell("learn_acc"), _cell("learn_f1_macro"),
                             f"p={p_learn_vs_rule:.3g}"],
    ]

    headers = ["Model", "Accuracy (mean ± std)", "F1 macro (mean ± std)", "McNemar vs Rule"]
    csv_p, tex_p = write_table(
        name="exp2_intent",
        headers=headers,
        rows=rows_out,
        caption=(
            f"Intent classification on the synthetic 500-utterance corpus "
            f"with a template-disjoint split, aggregated over "
            f"{len(SEEDS)} seeds."
        ),
        label="tab:intent",
    )
    append_manifest({
        "experiment": "exp2_intent",
        "seeds": list(SEEDS),
        "n_rows": len(rows),
        "aggregates": {k: {"mean": v[0], "std": v[1], "ci_low": v[2], "ci_high": v[3]}
                       for k, v in agg.items()},
        "csv": str(csv_p),
        "tex": str(tex_p),
    })
    return csv_p


if __name__ == "__main__":
    p = run()
    print(f"Exp.2 complete -> {p}")

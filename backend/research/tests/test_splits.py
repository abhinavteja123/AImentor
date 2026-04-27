"""Unit tests for the template-disjoint intent split used by Exp.2.

Ensures zero template leakage between train and test — this was the fix for the
Phase-1 F1=1.00 overfit where the classifier had seen every template at train
time.
"""

from __future__ import annotations

from backend.research.data_gen import gen_intents
from backend.research.experiments.exp2_intent_eval import _template_disjoint_split


def _synthetic_rows(n_templates_per_label: int = 10, per_template: int = 5):
    """Build a tiny labeled corpus with N templates × M variations per template."""
    rows = []
    labels = ["intent_a", "intent_b", "intent_c"]
    for lbl in labels:
        for t in range(n_templates_per_label):
            for _ in range(per_template):
                rows.append({
                    "text": f"{lbl} template {t} variant",
                    "intent": lbl,
                    "template_id": f"{lbl}#{t}",
                })
    return rows


def test_zero_template_leakage():
    rows = _synthetic_rows()
    train, test = _template_disjoint_split(rows, seed=42, heldout_per_label=2)
    train_ids = {r["template_id"] for r in train}
    test_ids = {r["template_id"] for r in test}
    # No template appears in both sets.
    assert train_ids.isdisjoint(test_ids)


def test_heldout_templates_per_label():
    rows = _synthetic_rows()
    _, test = _template_disjoint_split(rows, seed=42, heldout_per_label=2)
    per_label = {}
    for r in test:
        per_label.setdefault(r["intent"], set()).add(r["template_id"])
    # Every label contributes exactly 2 distinct held-out templates.
    for lbl, tids in per_label.items():
        assert len(tids) == 2, f"{lbl}: held out {tids}"


def test_split_is_deterministic_given_seed():
    rows = _synthetic_rows()
    tr1, te1 = _template_disjoint_split(rows, seed=7, heldout_per_label=2)
    tr2, te2 = _template_disjoint_split(rows, seed=7, heldout_per_label=2)
    assert [r["template_id"] for r in te1] == [r["template_id"] for r in te2]
    assert [r["template_id"] for r in tr1] == [r["template_id"] for r in tr2]


def test_different_seeds_pick_different_heldouts():
    rows = _synthetic_rows()
    _, te_a = _template_disjoint_split(rows, seed=1, heldout_per_label=2)
    _, te_b = _template_disjoint_split(rows, seed=999, heldout_per_label=2)
    ids_a = {r["template_id"] for r in te_a}
    ids_b = {r["template_id"] for r in te_b}
    # Not guaranteed to be fully disjoint, but should differ on at least one.
    assert ids_a != ids_b


def test_real_gen_intents_tags_templates():
    # Read the full 500-utterance corpus shipped with the repo and verify every
    # row is template-tagged. We DO NOT call gen_intents.generate() here — that
    # would overwrite the canonical dataset file used by Exp.2.
    import json
    from backend.research.config import DATASETS_DIR
    path = DATASETS_DIR / "intents_500.jsonl"
    if not path.exists():
        gen_intents.generate()
    with path.open("r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    assert rows, "intents_500.jsonl is empty"
    assert all("template_id" in r for r in rows)
    for r in rows[:50]:
        assert "#" in r["template_id"]
        lbl, idx = r["template_id"].split("#", 1)
        assert lbl == r["intent"]
        assert idx.isdigit()

"""Fine-tune DistilBERT for the AImentor 8-label intent taxonomy.

Training data options (``--dataset`` flag)::

    synthetic  — 500-utterance synthetic corpus (template-disjoint split)
    clinc150   — CLINC150's ``plus`` subset projected onto the 8-label map
    both       — synthetic train + clinc150 train, synthetic LOTO test

Usage::

    python -m backend.research.training.train_distilbert_intent \
        --dataset synthetic --seed 13 --epochs 3

Outputs::

    models/checkpoints/distilbert_intent_<dataset>_seed<seed>.pt
    models/checkpoints/distilbert_intent_<dataset>_seed<seed>.json   (training card)

The script is device-agnostic: it uses CUDA if available and falls back
to CPU. On CPU the 3-epoch run takes ~30 minutes for the synthetic
corpus — slow but finishes overnight.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import List, Tuple

from backend.research.config import DATASETS_DIR, INTENT_LABELS, MODEL_DISTILBERT
from backend.research.training.gpu_config import budget_for
from backend.research.training.train_utils import (
    CHECKPOINT_DIR,
    TrainingCard,
    get_device,
    log_gpu_memory,
    save_torch_state,
    set_all_seeds,
    timer_seconds,
)

LABEL_TO_ID = {lbl: i for i, lbl in enumerate(INTENT_LABELS)}
ID_TO_LABEL = {i: lbl for lbl, i in LABEL_TO_ID.items()}


def _load_rows(dataset: str) -> List[dict]:
    if dataset == "synthetic":
        with (DATASETS_DIR / "intents_500.jsonl").open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    if dataset == "clinc150":
        from backend.research.data_adapters.clinc150 import load as load_clinc
        return load_clinc(split="train", map_to_aimentor=True)
    if dataset == "both":
        from backend.research.data_adapters.clinc150 import load as load_clinc
        rows: List[dict] = []
        with (DATASETS_DIR / "intents_500.jsonl").open("r", encoding="utf-8") as f:
            rows.extend(json.loads(line) for line in f if line.strip())
        rows.extend(load_clinc(split="train", map_to_aimentor=True))
        return rows
    raise ValueError(f"unknown dataset '{dataset}'")


def _template_disjoint_split(rows: List[dict], seed: int) -> Tuple[List[dict], List[dict]]:
    """LOTO split; identical to the one in exp2_intent_eval."""
    from collections import defaultdict
    rng = random.Random(seed)
    by_label: dict = defaultdict(list)
    for r in rows:
        tid = r.get("template_id", "_legacy")
        lbl = r["intent"]
        if tid not in by_label[lbl]:
            by_label[lbl].append(tid)
    heldout: set = set()
    for lbl, tids in by_label.items():
        shuffled = sorted(tids)
        rng.shuffle(shuffled)
        for t in shuffled[:2]:
            heldout.add(t)
    train, test = [], []
    for r in rows:
        (test if r.get("template_id", "_legacy") in heldout else train).append(r)
    if not test:  # legacy corpus without template_ids
        rng = random.Random(seed)
        shuffled = list(rows)
        rng.shuffle(shuffled)
        cut = int(len(shuffled) * 0.8)
        return shuffled[:cut], shuffled[cut:]
    return train, test


def train(
    *,
    dataset: str = "synthetic",
    seed: int = 13,
    epochs: int = 3,
    lr: float = 2e-5,
    max_length: int = 96,
) -> Path:
    try:
        import torch  # type: ignore
        from torch.utils.data import DataLoader, Dataset
        from transformers import (  # type: ignore
            AutoModelForSequenceClassification,
            AutoTokenizer,
            get_linear_schedule_with_warmup,
        )
    except ImportError as e:
        raise RuntimeError(
            "Fine-tuning requires torch + transformers. "
            "`pip install -r backend/app/requirements-gpu.txt`"
        ) from e

    from sklearn.metrics import f1_score  # type: ignore

    set_all_seeds(seed)
    device = get_device()
    device_name = (
        torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu"
    )
    budget = budget_for(device_name)

    rows = _load_rows(dataset)
    train_rows, test_rows = _template_disjoint_split(rows, seed)
    print(f"[distilbert] dataset={dataset} n_train={len(train_rows)} "
          f"n_test={len(test_rows)} device={device_name}")

    tok = AutoTokenizer.from_pretrained(MODEL_DISTILBERT)

    class IntentDataset(Dataset):
        def __init__(self, rows):
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, i):
            r = self.rows[i]
            enc = tok(
                r["text"],
                max_length=max_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )
            return {
                "input_ids": enc["input_ids"].squeeze(0),
                "attention_mask": enc["attention_mask"].squeeze(0),
                "labels": torch.tensor(LABEL_TO_ID.get(r["intent"], 0), dtype=torch.long),
            }

    train_loader = DataLoader(IntentDataset(train_rows),
                              batch_size=budget.distilbert_train_bs,
                              shuffle=True)
    test_loader = DataLoader(IntentDataset(test_rows),
                             batch_size=budget.distilbert_train_bs)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DISTILBERT, num_labels=len(INTENT_LABELS)
    ).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    total_steps = max(1, epochs * len(train_loader))
    sched = get_linear_schedule_with_warmup(
        optim, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps
    )
    scaler = torch.cuda.amp.GradScaler() if budget.use_amp and device.type == "cuda" else None

    t0 = timer_seconds()
    best_f1 = -1.0
    best_epoch = -1
    for epoch in range(epochs):
        model.train()
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optim.zero_grad()
            if scaler is not None:
                with torch.cuda.amp.autocast():
                    out = model(**batch)
                scaler.scale(out.loss).backward()
                scaler.unscale_(optim)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optim)
                scaler.update()
            else:
                out = model(**batch)
                out.loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optim.step()
            sched.step()

        # validation
        model.eval()
        y_true, y_pred = [], []
        with torch.no_grad():
            for batch in test_loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                logits = model(input_ids=batch["input_ids"],
                               attention_mask=batch["attention_mask"]).logits
                y_true.extend(batch["labels"].tolist())
                y_pred.extend(logits.argmax(dim=-1).tolist())
        f1 = float(f1_score(y_true, y_pred, average="macro")) if y_true else 0.0
        print(f"[distilbert] epoch {epoch+1}/{epochs} val_f1_macro={f1:.4f}")
        if f1 > best_f1:
            best_f1, best_epoch = f1, epoch

    wall = timer_seconds() - t0
    log_gpu_memory("distilbert_post_train")

    ck_path = CHECKPOINT_DIR / f"distilbert_intent_{dataset}_seed{seed}.pt"
    save_torch_state(model, ck_path)
    TrainingCard(
        script="train_distilbert_intent",
        base_model=MODEL_DISTILBERT,
        dataset=dataset,
        seed=seed,
        epochs=epochs,
        batch_size=budget.distilbert_train_bs,
        lr=lr,
        device=device_name,
        val_metric=best_f1,
        wall_seconds=wall,
        extra={"best_epoch": best_epoch, "n_train": len(train_rows), "n_test": len(test_rows)},
    ).write(ck_path.with_suffix(".json"))
    return ck_path


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=["synthetic", "clinc150", "both"], default="synthetic")
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=2e-5)
    args = p.parse_args(argv)
    out = train(dataset=args.dataset, seed=args.seed, epochs=args.epochs, lr=args.lr)
    print(f"checkpoint -> {out}")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main() or 0)

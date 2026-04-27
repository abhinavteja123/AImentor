"""Fine-tune a cross-encoder reranker for resume/JD relevance.

Labels are soft (continuous O*NET-derived gold in [0, 1]) so we use BCE
with logits rather than a classification head. Hard negatives are drawn
from non-matching occupations with highest BM25 overlap against the
anchor.

Outputs::

    models/checkpoints/cross_encoder_seed<seed>/    (CrossEncoder dir)
    models/checkpoints/cross_encoder_seed<seed>.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import List, Tuple

from backend.research.config import MODEL_CROSS_ENCODER
from backend.research.data_adapters.onet import (
    gold_match,
    load_skill_ratings,
    occupation_skill_map,
)
from backend.research.training.gpu_config import budget_for
from backend.research.training.train_utils import (
    CHECKPOINT_DIR,
    TrainingCard,
    set_all_seeds,
    timer_seconds,
)


def _build_pairs(rng: random.Random, *, per_soc: int = 80) -> List[Tuple[str, str, float]]:
    ratings = load_skill_ratings()
    smap = occupation_skill_map(ratings)
    socs = list(smap.keys())
    pairs: List[Tuple[str, str, float]] = []
    for soc in socs:
        req = [s for s, _ in smap[soc]][:6]
        if not req:
            continue
        req_text = "; ".join(req)
        for _ in range(per_soc):
            # Positive — resume containing all required skills.
            pos_resume = "; ".join(req)
            gold_pos = gold_match(req, soc, smap)
            pairs.append((pos_resume, req_text, gold_pos))
            # Hard negative — resume drawn from a different SOC.
            neg_soc = rng.choice([o for o in socs if o != soc])
            neg_skills = [s for s, _ in smap[neg_soc]][:6]
            rng.shuffle(neg_skills)
            gold_neg = gold_match(neg_skills, soc, smap)
            pairs.append(("; ".join(neg_skills), req_text, gold_neg))
    rng.shuffle(pairs)
    return pairs


def train(*, seed: int = 13, epochs: int = 2, lr: float = 1e-5) -> Path:
    try:
        from sentence_transformers import CrossEncoder, InputExample  # type: ignore
        from torch.utils.data import DataLoader  # type: ignore
        import torch  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "Cross-encoder training requires sentence-transformers + torch."
        ) from e

    set_all_seeds(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    device_name = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"
    budget = budget_for(device_name)

    pairs = _build_pairs(random.Random(seed))
    print(f"[cross-encoder] pairs={len(pairs)} device={device_name}")
    if not pairs:
        raise RuntimeError("no pairs built; check O*NET fixture")

    examples = [InputExample(texts=[a, b], label=float(g)) for a, b, g in pairs]
    loader = DataLoader(examples, shuffle=True, batch_size=budget.cross_encoder_train_bs)

    model = CrossEncoder(MODEL_CROSS_ENCODER, num_labels=1, device=device)
    t0 = timer_seconds()
    model.fit(
        train_dataloader=loader,
        epochs=epochs,
        warmup_steps=max(1, int(0.1 * len(loader) * epochs)),
        optimizer_params={"lr": lr},
        use_amp=budget.use_amp and device == "cuda",
    )
    wall = timer_seconds() - t0

    out_dir = CHECKPOINT_DIR / f"cross_encoder_seed{seed}"
    model.save(str(out_dir))
    TrainingCard(
        script="train_cross_encoder",
        base_model=MODEL_CROSS_ENCODER,
        dataset="onet-derived-pairs",
        seed=seed,
        epochs=epochs,
        batch_size=budget.cross_encoder_train_bs,
        lr=lr,
        device=device_name,
        wall_seconds=wall,
        extra={"n_pairs": len(pairs)},
    ).write(CHECKPOINT_DIR / f"cross_encoder_seed{seed}.json")
    return out_dir


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--lr", type=float, default=1e-5)
    args = p.parse_args(argv)
    out = train(seed=args.seed, epochs=args.epochs, lr=args.lr)
    print(f"checkpoint -> {out}")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main() or 0)

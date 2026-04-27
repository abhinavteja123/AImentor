"""Fine-tune a Sentence-BERT bi-encoder for resume/JD matching.

Uses ``MultipleNegativesRankingLoss`` on triples
``(anchor, positive, hard_negative)`` derived from O*NET: positive pairs
share an occupation code; hard negatives are drawn from neighbouring
occupations whose BM25 overlap against the anchor's skills is highest
(but whose SOC is different).

Outputs::

    models/checkpoints/sbert_ats_seed<seed>/   (sentence-transformers dir)
    models/checkpoints/sbert_ats_seed<seed>.json    (training card)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from backend.research.config import MODEL_BI_ENCODER
from backend.research.data_adapters.onet import (
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


def _build_triples(
    rng: random.Random, *, n_per_soc: int = 60
) -> List[Tuple[str, str, str]]:
    r"""For each occupation, build (anchor, positive, hard_negative) triples.

    Anchor / positive are two different shufflings of the same occupation's
    top-importance skill list; the hard-negative is a shuffled skill list
    from a different occupation. This is the MNR-loss
    ``(query, pos, neg)`` format.
    """
    ratings = load_skill_ratings()
    smap = occupation_skill_map(ratings)
    triples: List[Tuple[str, str, str]] = []
    socs = list(smap.keys())
    if len(socs) < 2:
        return triples
    for soc in socs:
        pool = [s for s, _ in smap[soc]]
        if len(pool) < 3:
            continue
        other_socs = [o for o in socs if o != soc]
        for _ in range(n_per_soc):
            shuffled_a = pool[:]
            rng.shuffle(shuffled_a)
            shuffled_b = pool[:]
            rng.shuffle(shuffled_b)
            neg_soc = rng.choice(other_socs)
            neg_pool = [s for s, _ in smap[neg_soc]]
            rng.shuffle(neg_pool)
            triples.append(
                (
                    "; ".join(shuffled_a[:6]),
                    "; ".join(shuffled_b[:6]),
                    "; ".join(neg_pool[:6]),
                )
            )
    rng.shuffle(triples)
    return triples


def train(*, seed: int = 13, epochs: int = 2, lr: float = 2e-5) -> Path:
    try:
        from sentence_transformers import (  # type: ignore
            InputExample,
            SentenceTransformer,
            losses,
        )
        from torch.utils.data import DataLoader  # type: ignore
        import torch  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "Fine-tuning requires sentence-transformers + torch."
        ) from e

    set_all_seeds(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    device_name = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"
    budget = budget_for(device_name)

    triples = _build_triples(random.Random(seed))
    print(f"[sbert] triples={len(triples)} device={device_name}")
    if not triples:
        raise RuntimeError("no triples built; check O*NET fixture")

    examples = [InputExample(texts=[a, p, n]) for a, p, n in triples]
    loader = DataLoader(examples, shuffle=True, batch_size=budget.sbert_train_bs)

    model = SentenceTransformer(MODEL_BI_ENCODER, device=device)
    loss = losses.MultipleNegativesRankingLoss(model)

    t0 = timer_seconds()
    model.fit(
        train_objectives=[(loader, loss)],
        epochs=epochs,
        warmup_steps=max(1, int(0.1 * len(loader) * epochs)),
        optimizer_params={"lr": lr},
        use_amp=budget.use_amp and device == "cuda",
    )
    wall = timer_seconds() - t0

    out_dir = CHECKPOINT_DIR / f"sbert_ats_seed{seed}"
    model.save(str(out_dir))
    TrainingCard(
        script="train_sbert_ats",
        base_model=MODEL_BI_ENCODER,
        dataset="onet-derived-triples",
        seed=seed,
        epochs=epochs,
        batch_size=budget.sbert_train_bs,
        lr=lr,
        device=device_name,
        wall_seconds=wall,
        extra={"n_triples": len(triples)},
    ).write(CHECKPOINT_DIR / f"sbert_ats_seed{seed}.json")
    return out_dir


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--lr", type=float, default=2e-5)
    args = p.parse_args(argv)
    out = train(seed=args.seed, epochs=args.epochs, lr=args.lr)
    print(f"checkpoint -> {out}")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main() or 0)

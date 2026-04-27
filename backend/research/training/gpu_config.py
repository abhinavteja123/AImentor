"""Hardware-aware batch-size and precision hints for Phase-B training.

V100 (32 GB) is the reference target; other devices downscale the batch.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelBudget:
    distilbert_train_bs: int
    sbert_train_bs: int
    cross_encoder_train_bs: int
    use_amp: bool


V100_32GB = ModelBudget(
    distilbert_train_bs=64,
    sbert_train_bs=128,
    cross_encoder_train_bs=32,
    use_amp=True,
)

T4_16GB = ModelBudget(
    distilbert_train_bs=32,
    sbert_train_bs=64,
    cross_encoder_train_bs=16,
    use_amp=True,
)

CPU_FALLBACK = ModelBudget(
    distilbert_train_bs=8,
    sbert_train_bs=16,
    cross_encoder_train_bs=4,
    use_amp=False,
)


def budget_for(device_name: str) -> ModelBudget:
    name = (device_name or "").lower()
    if "v100" in name:
        return V100_32GB
    if "t4" in name or "p100" in name or "p40" in name:
        return T4_16GB
    return CPU_FALLBACK

"""Shared helpers for the Phase-B fine-tuning scripts."""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional

CHECKPOINT_DIR = Path(__file__).resolve().parents[1] / "models" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def prefer_gpu() -> bool:
    """Opt-in GPU flag consumed by every training script.

    Respects the ``AIMENTOR_PREFER_GPU=1`` env var set by ``run_all``.
    Even when set, we always fall back to CPU when CUDA is unavailable.
    """
    if os.environ.get("AIMENTOR_PREFER_GPU") != "1":
        return False
    try:
        import torch  # type: ignore
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def get_device(prefer_cuda: bool = True):
    """Return the best available torch device. Requires torch."""
    import torch  # type: ignore
    if prefer_cuda and torch.cuda.is_available():
        return torch.device("cuda:0")
    return torch.device("cpu")


def set_all_seeds(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np  # type: ignore
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch  # type: ignore
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def log_gpu_memory(prefix: str = "") -> Optional[Dict[str, float]]:
    try:
        import torch  # type: ignore
        if not torch.cuda.is_available():
            return None
        props = torch.cuda.get_device_properties(0)
        alloc = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        info = {
            "gpu": props.name,
            "total_gb": round(props.total_memory / 1024**3, 2),
            "alloc_gb": round(alloc, 2),
            "reserved_gb": round(reserved, 2),
        }
        if prefix:
            print(f"[{prefix}] {info}")
        return info
    except Exception:
        return None


@dataclass
class TrainingCard:
    script: str
    base_model: str
    dataset: str
    seed: int
    epochs: int
    batch_size: int
    lr: float
    device: str
    val_metric: Optional[float] = None
    wall_seconds: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def write(self, path: Path) -> None:
        def _default(o):
            if is_dataclass(o):
                return asdict(o)
            return str(o)
        path.write_text(json.dumps(asdict(self), default=_default, indent=2),
                        encoding="utf-8")


def timer_seconds() -> float:
    return time.time()


def save_torch_state(model, out_path: Path) -> None:
    """Save just the state_dict — easier to reload into a fresh model shell."""
    import torch  # type: ignore
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_path)

"""CLINC150 public intent-classification benchmark adapter.

Reference
---------
Larson, Mahendran, Peper, Clarke, Lee, Hill, Kummerfeld, Leach, Laurenzano,
Tang, Mars (2019). *An Evaluation Dataset for Intent Classification and
Out-of-Scope Prediction.* EMNLP. https://aclanthology.org/D19-1131/

The dataset ships 150 in-domain intents plus one ``oos`` label. We use the
``clinc_oos`` subset ``plus`` (larger + includes OOS) via HuggingFace
``datasets``. Rows are emitted in the same schema as AImentor's synthetic
intents corpus::

    {"text": str, "intent": str, "template_id": str, "source": "clinc150"}

A hand-curated coarse map at ``datasets/mappings/clinc150_to_aimentor.json``
projects CLINC's 151 labels onto the 8-label AImentor taxonomy. Intents not
listed in the map fall into ``general_chat``. Callers that want native
CLINC labels pass ``map_to_aimentor=False``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from backend.research.config import DATASETS_DIR, INTENT_LABELS

CACHE_DIR = DATASETS_DIR / "cache" / "clinc150"
MAPPING_PATH = DATASETS_DIR / "mappings" / "clinc150_to_aimentor.json"


def _load_mapping() -> Dict[str, str]:
    with MAPPING_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    m = raw["map"]
    for k, v in m.items():
        if v not in INTENT_LABELS:
            raise ValueError(f"mapping target '{v}' for '{k}' is not a valid AImentor label")
    return m


def load(
    split: str = "test",
    *,
    map_to_aimentor: bool = True,
    subset: str = "plus",
    limit: Optional[int] = None,
) -> List[Dict[str, str]]:
    """Return CLINC150 rows in AImentor schema.

    Parameters
    ----------
    split:
        ``train``, ``validation``, or ``test``. ``plus`` has all three.
    map_to_aimentor:
        If True (default), project native CLINC intents onto the 8-label
        AImentor taxonomy via the hand map. If False, return native
        CLINC intent strings so the dataset can be trained natively.
    subset:
        ``plus`` (default) — the standard 150-intent + OOS release.
    limit:
        Truncate to the first ``limit`` rows (after mapping). Used in tests.
    """
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as e:  # pragma: no cover - install-time
        raise RuntimeError(
            "huggingface 'datasets' not installed; `pip install datasets`"
        ) from e

    ds = load_dataset("clinc_oos", subset, cache_dir=str(CACHE_DIR))
    if split not in ds:
        raise KeyError(f"split '{split}' not in clinc_oos/{subset}; have {list(ds)}")

    intent_names = ds[split].features["intent"].names  # List[str]
    mapping = _load_mapping() if map_to_aimentor else None

    rows: List[Dict[str, str]] = []
    for i, ex in enumerate(ds[split]):
        native = intent_names[ex["intent"]]
        if mapping is not None:
            label = mapping.get(native, "general_chat")
        else:
            label = native
        rows.append(
            {
                "text": ex["text"],
                "intent": label,
                "template_id": f"clinc150#{native}",
                "source": "clinc150",
                "native_intent": native,
            }
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


def save_jsonl(
    out_path: Path,
    *,
    split: str = "test",
    map_to_aimentor: bool = True,
    subset: str = "plus",
) -> int:
    """Materialize a CLINC150 split to JSONL. Returns the number of rows."""
    rows = load(split=split, map_to_aimentor=map_to_aimentor, subset=subset)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return len(rows)


if __name__ == "__main__":  # pragma: no cover - ops convenience
    for split in ("train", "validation", "test"):
        n = save_jsonl(
            DATASETS_DIR / f"clinc150_{split}.jsonl",
            split=split,
            map_to_aimentor=True,
        )
        print(f"wrote {n} rows to clinc150_{split}.jsonl")

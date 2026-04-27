"""BANKING77 public intent-classification benchmark adapter.

Reference
---------
Casanueva, Temcinas, Gerz, Henderson, Vulic (2020). *Efficient Intent
Detection with Dual Sentence Encoders.* ACL-NLP4ConvAI.
https://aclanthology.org/2020.nlp4convai-1.5/

The HuggingFace script loader for ``PolyAI/banking77`` was deprecated in
``datasets>=4.0`` (no-script repos only). We therefore fetch the canonical
CSVs directly from the PolyAI public GitHub mirror and cache them locally,
keeping this adapter compatible across library versions.
"""

from __future__ import annotations

import csv
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from backend.research.config import DATASETS_DIR, INTENT_LABELS

CACHE_DIR = DATASETS_DIR / "cache" / "banking77"
MAPPING_PATH = DATASETS_DIR / "mappings" / "banking77_to_aimentor.json"

_SOURCE = (
    "https://raw.githubusercontent.com/PolyAI-LDN/"
    "task-specific-datasets/master/banking_data"
)
_FILES = {"train": "train.csv", "test": "test.csv"}


def _load_mapping() -> Dict[str, str]:
    with MAPPING_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    m = raw["map"]
    for k, v in m.items():
        if v not in INTENT_LABELS:
            raise ValueError(f"mapping target '{v}' for '{k}' is not a valid AImentor label")
    return m


def _ensure_cached(split: str) -> Path:
    if split not in _FILES:
        raise KeyError(f"split '{split}' not in {list(_FILES)}")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / _FILES[split]
    if not dest.exists():
        url = f"{_SOURCE}/{_FILES[split]}"
        urllib.request.urlretrieve(url, dest)
    return dest


def load(
    split: str = "test",
    *,
    map_to_aimentor: bool = True,
    limit: Optional[int] = None,
) -> List[Dict[str, str]]:
    path = _ensure_cached(split)
    mapping = _load_mapping() if map_to_aimentor else None

    out: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for ex in r:
            native = (ex.get("category") or "").strip()
            text = (ex.get("text") or "").strip()
            if not native or not text:
                continue
            label = (mapping.get(native, "general_chat") if mapping is not None else native)
            out.append(
                {
                    "text": text,
                    "intent": label,
                    "template_id": f"banking77#{native}",
                    "source": "banking77",
                    "native_intent": native,
                }
            )
            if limit is not None and len(out) >= limit:
                break
    return out


def save_jsonl(out_path: Path, *, split: str = "test", map_to_aimentor: bool = True) -> int:
    rows = load(split=split, map_to_aimentor=map_to_aimentor)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return len(rows)


if __name__ == "__main__":  # pragma: no cover
    for split in ("train", "test"):
        n = save_jsonl(DATASETS_DIR / f"banking77_{split}.jsonl", split=split)
        print(f"wrote {n} rows to banking77_{split}.jsonl")

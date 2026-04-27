"""Public-dataset adapters for the AImentor research harness.

Each adapter returns rows in the same schema as the corresponding synthetic
dataset so the experiment runners can swap sources with a single ``--dataset``
flag. Raw files are cached under ``datasets/cache/`` and large Kaggle dumps
are expected at ``datasets/external/`` (not auto-downloaded to respect TOS).
"""

from __future__ import annotations

__all__ = [
    "clinc150",
    "banking77",
    "onet",
    "resumes",
    "jobs",
]

"""Fine-tuning entry points for the research harness.

All scripts are device-agnostic: they prefer CUDA if available and fall
back to CPU otherwise. Each writes a checkpoint under
``models/checkpoints/`` plus a JSON card describing the training
configuration, dataset, and final validation metric.
"""

from __future__ import annotations

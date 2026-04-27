"""AImentor research workspace — evaluation harness, datasets, and experiments
supporting the IEEE conference submission.

Runtime note: every experiment defaults to *offline* execution so reviewers can
reproduce the tables without needing live LLM keys or Supabase access.
Pass ``--live`` to any runner to hit real providers.
"""

__version__ = "0.1.0"

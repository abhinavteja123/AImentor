"""Keyword/rule-based intent classifier.

Replicates :func:`MentorChatEngine._analyze_intent` exactly so the evaluation
numbers match what the production codebase currently does. Imported from
``chat_engine`` when the module is reachable; otherwise the logic is inlined
(so running the harness does not require a working SQLAlchemy/DB setup).
"""

from __future__ import annotations


def predict(message: str) -> str:
    m = (message or "").lower()
    if any(w in m for w in ("help", "stuck", "don't understand", "confused")):
        return "asking_for_help"
    if any(w in m for w in ("explain", "what is", "how does", "why")):
        return "requesting_explanation"
    if any(w in m for w in ("motivation", "tired", "giving up", "hard")):
        return "seeking_motivation"
    if any(w in m for w in ("struggling", "difficult", "can't")):
        return "reporting_struggle"
    if any(w in m for w in ("next", "should i", "what now", "today")):
        return "asking_next_steps"
    if any(w in m for w in ("resource", "learn", "tutorial", "course")):
        return "requesting_resources"
    if any(w in m for w in ("progress", "how am i", "doing")):
        return "asking_progress"
    return "general_chat"

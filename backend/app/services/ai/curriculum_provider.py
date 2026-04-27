"""
Curriculum Provider seam.

RoadmapGenerator currently returns hardcoded week-by-week curricula from
giant if/elif tables. This module introduces a strategy interface so we can
swap in a real LLM-generated curriculum without rewriting RoadmapGenerator.

Use `get_curriculum_provider()` to obtain the configured implementation
(toggle via settings.USE_LLM_CURRICULUM).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class CurriculumProvider(Protocol):
    async def get_skill_curriculum(self, skill_name: str) -> List[Dict[str, Any]]: ...


class HardcodedCurriculumProvider:
    """Wraps the existing hardcoded curriculum function. No behavior change."""

    def __init__(self, fallback_fn: Callable[[str], List[Dict[str, Any]]]):
        self._fn = fallback_fn

    async def get_skill_curriculum(self, skill_name: str) -> List[Dict[str, Any]]:
        return self._fn(skill_name)


class LLMCurriculumProvider:
    """Generates curricula via Gemini with a fallback on failure."""

    SYSTEM_PROMPT = (
        "You are a senior curriculum designer. Produce a concrete, week-by-week "
        "plan for learning one skill. Each week has exactly 7 daily tasks. "
        "Each task has fields: day (1-7), title, type (reading|coding|project), desc. "
        "Return JSON only, matching the schema the user provides."
    )

    USER_TEMPLATE = (
        "Skill: {skill}\n"
        "Audience: beginner-to-intermediate self-learner, ~1 hr/day.\n"
        "Produce 3-4 weeks of progressive content.\n\n"
        "Respond with JSON of shape:\n"
        '{{"weeks": [{{"week_topic": "...", "tasks": [{{"day": 1, "title": "...", "type": "coding", "desc": "..."}}]}}]}}'
    )

    def __init__(
        self,
        llm_client: Any,
        fallback: Optional[CurriculumProvider] = None,
    ):
        self._llm = llm_client
        self._fallback = fallback

    async def get_skill_curriculum(self, skill_name: str) -> List[Dict[str, Any]]:
        try:
            payload = await self._llm.generate_json(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=self.USER_TEMPLATE.format(skill=skill_name),
                temperature=0.4,
            )
            weeks = payload.get("weeks") if isinstance(payload, dict) else None
            if not isinstance(weeks, list) or not weeks:
                raise ValueError("LLM returned no weeks")
            return weeks
        except Exception as exc:
            logger.warning("LLM curriculum failed for %r: %s", skill_name, exc)
            if self._fallback is not None:
                return await self._fallback.get_skill_curriculum(skill_name)
            raise


def get_curriculum_provider(
    hardcoded_fn: Callable[[str], List[Dict[str, Any]]],
    llm_client: Optional[Any] = None,
    use_llm: Optional[bool] = None,
) -> CurriculumProvider:
    """
    Factory. Returns LLMCurriculumProvider (with hardcoded fallback) when the
    feature flag is on and an LLM client is available; hardcoded otherwise.
    """
    from ...config import settings

    if use_llm is None:
        use_llm = bool(getattr(settings, "USE_LLM_CURRICULUM", False))

    hardcoded = HardcodedCurriculumProvider(hardcoded_fn)
    if use_llm and llm_client is not None:
        return LLMCurriculumProvider(llm_client, fallback=hardcoded)
    return hardcoded

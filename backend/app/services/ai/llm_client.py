"""
LLMClient — thin facade over the LLMProvider fallback chain.

Call sites (skill_analyzer, chat_engine, roadmap_generator, resume_service,
curriculum_provider) all import `LLMClient` or `get_llm_client()`. Keeping
this surface stable means we can swap the underlying provider layer without
touching any of them.

Methods:
- generate_completion(system_prompt, user_prompt, ...) -> str
- generate_with_context(prompt, context, ...) -> str
- generate_json(system_prompt, user_prompt, ...) -> dict
- generate_text(prompt, ...) -> str           (resume_service)
- chat_completion(messages, ...) -> str       (chat_engine)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .llm_provider import FallbackChain, LLMFatalError, build_default_chain

logger = logging.getLogger(__name__)


class LLMClient:
    """Stable facade. Behaviour is delegated to a provider chain."""

    def __init__(self, chain: Optional[FallbackChain] = None):
        self._chain = chain or build_default_chain()

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[str] = None,
    ) -> str:
        if response_format == "json":
            user_prompt = f"{user_prompt}\n\nRespond with valid JSON only, no markdown formatting."
        return await self._chain.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        temperature: float = 0.7,
    ) -> str:
        system_prompt = (
            "You are an AI career mentor assistant. Use the provided context to give "
            "personalized, helpful responses. Be encouraging, specific, and actionable."
        )
        context_str = json.dumps(context, indent=2, default=str)
        user_prompt = f"Context:\n{context_str}\n\nQuery: {prompt}\n\nProvide a helpful, personalized response."
        return await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        response = await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format="json",
            max_tokens=4000,
        )
        return _parse_json_response(response)

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Single-prompt convenience wrapper. Used by resume_service."""
        return await self.generate_completion(
            system_prompt="You are a helpful assistant for resume and career content generation.",
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        return await self._chain.chat(
            messages=messages, temperature=temperature, max_tokens=max_tokens
        )


def _parse_json_response(response: str) -> Dict[str, Any]:
    """Strip markdown code fences and extract JSON. Mirrors old behaviour."""
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        raise


# Singleton — built lazily so tests can inject a custom client.
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def reset_llm_client() -> None:
    """Drop the cached singleton — used by tests."""
    global _llm_client
    _llm_client = None

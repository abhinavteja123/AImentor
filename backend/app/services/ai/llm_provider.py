"""
LLM provider abstraction with automatic fallback on rate-limits / transient errors.

Design:
- One `LLMProvider` protocol exposing `complete(system, user, ...)` and
  `chat(messages, ...)`.
- `OpenAICompatibleProvider` covers Groq + Cerebras (both speak the OpenAI
  chat-completions REST shape). Uses httpx directly — no heavyweight SDK.
- `GeminiProvider` wraps google-generativeai for the same interface.
- `FallbackChain` tries providers in order. On 429 / 5xx / network errors it
  falls through to the next; on hard 4xx it raises immediately.
- `build_default_chain()` reads settings and returns the configured chain.

The existing `LLMClient` in `llm_client.py` is rewired to delegate to this
chain, so every caller (skill_analyzer, chat_engine, roadmap_generator,
resume_service) keeps working unchanged.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Protocol

import httpx

logger = logging.getLogger(__name__)


def _log_attempt(provider: str, method: str, outcome: str, latency_ms: int, err: str = "") -> None:
    """Single structured line per provider attempt. Greppable by 'llm.attempt'."""
    err_part = f' err="{err[:160]}"' if err else ""
    logger.info(
        "llm.attempt provider=%s method=%s outcome=%s latency_ms=%d%s",
        provider, method, outcome, latency_ms, err_part,
    )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """Base error for the provider layer."""


class LLMRateLimitError(LLMError):
    """429 or provider-specific quota exhaustion — fallback-eligible."""


class LLMTransientError(LLMError):
    """5xx / network — fallback-eligible."""


class LLMFatalError(LLMError):
    """4xx (not 429) — don't fall back, surface to caller."""


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str: ...

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str: ...


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (Groq, Cerebras, Together, Ollama, etc.)
# ---------------------------------------------------------------------------


class OpenAICompatibleProvider:
    """
    Any provider that implements POST /chat/completions with OpenAI's schema.
    Works for Groq, Cerebras, Together, Ollama, OpenAI, etc.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 45.0,
    ):
        if not api_key:
            raise ValueError(f"{name}: api_key is required")
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return await self.chat(messages, temperature, max_tokens)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = await self._client.post(
                f"{self._base_url}/chat/completions", json=payload
            )
        except httpx.TimeoutException as e:
            raise LLMTransientError(f"{self.name} timeout: {e}") from e
        except httpx.HTTPError as e:
            raise LLMTransientError(f"{self.name} network error: {e}") from e

        if resp.status_code == 429:
            raise LLMRateLimitError(f"{self.name} rate-limited: {resp.text[:200]}")
        if 500 <= resp.status_code < 600:
            raise LLMTransientError(f"{self.name} {resp.status_code}: {resp.text[:200]}")
        if resp.status_code >= 400:
            raise LLMFatalError(f"{self.name} {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMFatalError(f"{self.name} malformed response: {e} body={resp.text[:200]}") from e


# ---------------------------------------------------------------------------
# Gemini (google-generativeai)
# ---------------------------------------------------------------------------


class GeminiProvider:
    """Adapts google-generativeai to the LLMProvider protocol."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("gemini: api_key is required")
        self.name = "gemini"
        self._model_name = model
        # Lazy import so the provider layer doesn't require google-generativeai
        # when it's not configured.
        import google.generativeai as genai  # type: ignore

        self._genai = genai
        self._genai.configure(api_key=api_key)
        self._safety_settings = [
            {"category": c, "threshold": "BLOCK_NONE"}
            for c in (
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
            )
        ]

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.95,
                "top_k": 40,
            },
            safety_settings=self._safety_settings,
            system_instruction=system_prompt or None,
        )
        try:
            response = await model.generate_content_async(user_prompt)
            return response.text
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg or "429" in msg or "resource" in msg:
                raise LLMRateLimitError(f"gemini rate-limited: {e}") from e
            raise LLMTransientError(f"gemini error: {e}") from e

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        system_instruction: Optional[str] = None
        chat_messages: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            elif role == "user":
                chat_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                chat_messages.append({"role": "model", "parts": [content]})

        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
            safety_settings=self._safety_settings,
            system_instruction=system_instruction,
        )
        try:
            chat = model.start_chat(
                history=chat_messages[:-1] if len(chat_messages) > 1 else []
            )
            last = chat_messages[-1]["parts"][0] if chat_messages else ""
            response = await chat.send_message_async(last)
            return response.text
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg or "429" in msg or "resource" in msg:
                raise LLMRateLimitError(f"gemini rate-limited: {e}") from e
            raise LLMTransientError(f"gemini error: {e}") from e


# ---------------------------------------------------------------------------
# Fallback chain
# ---------------------------------------------------------------------------


class FallbackChain:
    """
    Try each provider in order. Fall through on rate-limit or transient errors;
    raise immediately on fatal (4xx non-429) errors or when all providers are
    exhausted.
    """

    def __init__(self, providers: List[LLMProvider]):
        if not providers:
            raise ValueError("FallbackChain requires at least one provider")
        self._providers = providers
        self.name = "fallback(" + "+".join(p.name for p in providers) + ")"

    async def complete(self, system_prompt, user_prompt, temperature, max_tokens) -> str:
        return await self._run("complete", system_prompt, user_prompt, temperature, max_tokens)

    async def chat(self, messages, temperature, max_tokens) -> str:
        return await self._run("chat", messages, temperature, max_tokens)

    async def _run(self, method: str, *args: Any) -> str:
        last_exc: Optional[Exception] = None
        for p in self._providers:
            start = time.monotonic()
            try:
                fn = getattr(p, method)
                result = await fn(*args)
                _log_attempt(p.name, method, "ok", int((time.monotonic() - start) * 1000))
                if last_exc:
                    logger.info("llm: recovered via %s after %s", p.name, type(last_exc).__name__)
                return result
            except LLMFatalError as e:
                _log_attempt(p.name, method, "fatal", int((time.monotonic() - start) * 1000), str(e))
                raise
            except (LLMRateLimitError, LLMTransientError) as e:
                outcome = "rate_limit" if isinstance(e, LLMRateLimitError) else "transient"
                _log_attempt(p.name, method, outcome, int((time.monotonic() - start) * 1000), str(e))
                last_exc = e
                continue
        assert last_exc is not None
        raise last_exc


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def _build_provider(name: str, settings: Any) -> Optional[LLMProvider]:
    try:
        if name == "groq":
            return OpenAICompatibleProvider(
                name="groq",
                base_url="https://api.groq.com/openai/v1",
                api_key=getattr(settings, "GROQ_API_KEY", ""),
                model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
            )
        if name == "cerebras":
            return OpenAICompatibleProvider(
                name="cerebras",
                base_url="https://api.cerebras.ai/v1",
                api_key=getattr(settings, "CEREBRAS_API_KEY", ""),
                model=getattr(settings, "CEREBRAS_MODEL", "llama-3.3-70b"),
            )
        if name == "gemini":
            return GeminiProvider(
                api_key=getattr(settings, "GOOGLE_API_KEY", ""),
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash-exp"),
            )
    except ValueError as e:
        logger.info("llm: skipping %s provider (not configured): %s", name, e)
        return None
    return None


def build_default_chain(settings: Any = None) -> FallbackChain:
    """Build a chain based on settings. Primary first, fallbacks after."""
    if settings is None:
        from ...config import settings as _s
        settings = _s

    primary_name = getattr(settings, "LLM_PROVIDER", "groq").lower()
    order = [primary_name] + [p for p in ("groq", "cerebras", "gemini") if p != primary_name]
    providers: List[LLMProvider] = []
    seen: set[str] = set()
    for name in order:
        if name in seen:
            continue
        seen.add(name)
        p = _build_provider(name, settings)
        if p is not None:
            providers.append(p)

    if not providers:
        raise RuntimeError(
            "No LLM providers configured. Set at least one of "
            "GROQ_API_KEY / CEREBRAS_API_KEY / GOOGLE_API_KEY."
        )
    logger.info("llm: chain = %s", " -> ".join(p.name for p in providers))
    return FallbackChain(providers)

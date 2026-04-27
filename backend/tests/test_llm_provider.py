"""
Unit tests for the LLM provider layer. No network — uses httpx mock transport
for the OpenAI-compatible provider and fakes for the chain.
"""

import httpx
import pytest

from app.services.ai.llm_provider import (
    FallbackChain,
    LLMFatalError,
    LLMRateLimitError,
    LLMTransientError,
    OpenAICompatibleProvider,
    build_default_chain,
)


# ----- httpx mocked transport helpers --------------------------------------


def _make_provider(status: int, body: dict | str = None) -> OpenAICompatibleProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(body, dict):
            return httpx.Response(status, json=body)
        return httpx.Response(status, text=body or "")

    p = OpenAICompatibleProvider(
        name="test",
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model="test-model",
    )
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return p


# ----- OpenAICompatibleProvider --------------------------------------------


async def test_provider_returns_text_on_200():
    p = _make_provider(
        200, {"choices": [{"message": {"content": "hello world"}}]}
    )
    out = await p.complete("sys", "user", temperature=0.1, max_tokens=10)
    assert out == "hello world"


async def test_provider_raises_rate_limit_on_429():
    p = _make_provider(429, "quota exceeded")
    with pytest.raises(LLMRateLimitError):
        await p.complete("sys", "user", temperature=0.1, max_tokens=10)


async def test_provider_raises_transient_on_502():
    p = _make_provider(502, "bad gateway")
    with pytest.raises(LLMTransientError):
        await p.complete("sys", "user", temperature=0.1, max_tokens=10)


async def test_provider_raises_fatal_on_401():
    p = _make_provider(401, "bad key")
    with pytest.raises(LLMFatalError):
        await p.complete("sys", "user", temperature=0.1, max_tokens=10)


async def test_provider_raises_fatal_on_malformed_response():
    p = _make_provider(200, {"wrong": "shape"})
    with pytest.raises(LLMFatalError):
        await p.complete("sys", "user", temperature=0.1, max_tokens=10)


def test_provider_requires_api_key():
    with pytest.raises(ValueError):
        OpenAICompatibleProvider(
            name="x", base_url="https://x/v1", api_key="", model="m"
        )


# ----- FallbackChain --------------------------------------------------------


class _FakeProvider:
    def __init__(self, name: str, on_call):
        self.name = name
        self._on_call = on_call
        self.call_count = 0

    async def complete(self, *args, **kwargs):
        self.call_count += 1
        return await self._on_call(*args, **kwargs)

    async def chat(self, *args, **kwargs):
        self.call_count += 1
        return await self._on_call(*args, **kwargs)


async def _returns(text: str):
    async def _call(*a, **kw):
        return text
    return _call


async def _raises(exc: Exception):
    async def _call(*a, **kw):
        raise exc
    return _call


async def test_chain_returns_first_success():
    a = _FakeProvider("a", await _returns("A"))
    b = _FakeProvider("b", await _returns("B"))
    chain = FallbackChain([a, b])
    assert await chain.complete("s", "u", 0.1, 10) == "A"
    assert a.call_count == 1
    assert b.call_count == 0


async def test_chain_falls_through_on_rate_limit():
    a = _FakeProvider("a", await _raises(LLMRateLimitError("quota")))
    b = _FakeProvider("b", await _returns("B"))
    chain = FallbackChain([a, b])
    assert await chain.complete("s", "u", 0.1, 10) == "B"
    assert a.call_count == 1
    assert b.call_count == 1


async def test_chain_falls_through_on_transient():
    a = _FakeProvider("a", await _raises(LLMTransientError("502")))
    b = _FakeProvider("b", await _returns("B"))
    chain = FallbackChain([a, b])
    assert await chain.complete("s", "u", 0.1, 10) == "B"


async def test_chain_raises_fatal_immediately_without_fallback():
    a = _FakeProvider("a", await _raises(LLMFatalError("401")))
    b = _FakeProvider("b", await _returns("B"))
    chain = FallbackChain([a, b])
    with pytest.raises(LLMFatalError):
        await chain.complete("s", "u", 0.1, 10)
    assert b.call_count == 0  # never tried


async def test_chain_raises_last_error_when_all_exhausted():
    a = _FakeProvider("a", await _raises(LLMRateLimitError("a")))
    b = _FakeProvider("b", await _raises(LLMRateLimitError("b")))
    chain = FallbackChain([a, b])
    with pytest.raises(LLMRateLimitError):
        await chain.complete("s", "u", 0.1, 10)


def test_chain_requires_at_least_one_provider():
    with pytest.raises(ValueError):
        FallbackChain([])


# ----- build_default_chain --------------------------------------------------


class _Settings:
    def __init__(self, **kw):
        self.LLM_PROVIDER = kw.get("LLM_PROVIDER", "groq")
        self.GROQ_API_KEY = kw.get("GROQ_API_KEY", "")
        self.GROQ_MODEL = "llama-3.3-70b-versatile"
        self.CEREBRAS_API_KEY = kw.get("CEREBRAS_API_KEY", "")
        self.CEREBRAS_MODEL = "llama-3.3-70b"
        self.GOOGLE_API_KEY = kw.get("GOOGLE_API_KEY", "")
        self.GEMINI_MODEL = "gemini-2.0-flash-exp"


def test_build_chain_orders_primary_first():
    s = _Settings(LLM_PROVIDER="cerebras", GROQ_API_KEY="g", CEREBRAS_API_KEY="c")
    chain = build_default_chain(s)
    names = [p.name for p in chain._providers]
    assert names[0] == "cerebras"
    assert "groq" in names


def test_build_chain_skips_unconfigured_providers():
    s = _Settings(LLM_PROVIDER="groq", GROQ_API_KEY="g")  # cerebras, gemini missing
    chain = build_default_chain(s)
    names = [p.name for p in chain._providers]
    assert names == ["groq"]


def test_build_chain_raises_when_none_configured():
    s = _Settings()
    with pytest.raises(RuntimeError):
        build_default_chain(s)

"""
Surface-level checks on LLMClient: all methods called by the rest of the app
exist and have the expected signatures. Would have caught the generate_text
AttributeError bug in resume_service.py.
"""

import inspect

from app.services.ai.llm_client import LLMClient


REQUIRED_METHODS = {
    "generate_completion",
    "generate_with_context",
    "generate_json",
    "generate_text",
    "chat_completion",
}


def test_llm_client_exposes_all_methods_used_by_callers():
    missing = REQUIRED_METHODS - set(dir(LLMClient))
    assert not missing, f"LLMClient is missing methods its callers use: {missing}"


def test_generate_text_is_coroutine():
    assert inspect.iscoroutinefunction(LLMClient.generate_text)


def test_generate_text_accepts_prompt_temperature_max_tokens():
    sig = inspect.signature(LLMClient.generate_text)
    params = sig.parameters
    assert "prompt" in params
    assert "temperature" in params
    assert "max_tokens" in params

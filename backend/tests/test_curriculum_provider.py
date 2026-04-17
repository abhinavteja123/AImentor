import pytest

from app.services.ai.curriculum_provider import (
    HardcodedCurriculumProvider,
    LLMCurriculumProvider,
    get_curriculum_provider,
)


def _fake_hardcoded(skill: str):
    return [{"week_topic": f"{skill} week 1", "tasks": []}]


class FakeLLM:
    def __init__(self, payload=None, raise_exc=None):
        self.payload = payload
        self.raise_exc = raise_exc
        self.calls = 0

    async def generate_json(self, system_prompt, user_prompt, temperature=0.7):
        self.calls += 1
        if self.raise_exc:
            raise self.raise_exc
        return self.payload


async def test_hardcoded_provider_delegates_to_fallback_fn():
    provider = HardcodedCurriculumProvider(_fake_hardcoded)
    result = await provider.get_skill_curriculum("python")
    assert result == [{"week_topic": "python week 1", "tasks": []}]


async def test_llm_provider_returns_weeks_on_success():
    llm = FakeLLM(payload={"weeks": [{"week_topic": "Rust w1", "tasks": []}]})
    provider = LLMCurriculumProvider(llm)
    result = await provider.get_skill_curriculum("rust")
    assert llm.calls == 1
    assert result[0]["week_topic"] == "Rust w1"


async def test_llm_provider_falls_back_on_exception():
    llm = FakeLLM(raise_exc=RuntimeError("quota exceeded"))
    fallback = HardcodedCurriculumProvider(_fake_hardcoded)
    provider = LLMCurriculumProvider(llm, fallback=fallback)
    result = await provider.get_skill_curriculum("go")
    assert result[0]["week_topic"] == "go week 1"


async def test_llm_provider_falls_back_on_empty_weeks():
    llm = FakeLLM(payload={"weeks": []})
    fallback = HardcodedCurriculumProvider(_fake_hardcoded)
    provider = LLMCurriculumProvider(llm, fallback=fallback)
    result = await provider.get_skill_curriculum("kotlin")
    assert result[0]["week_topic"] == "kotlin week 1"


async def test_llm_provider_raises_when_no_fallback_and_bad_payload():
    llm = FakeLLM(payload={"not_weeks": 1})
    provider = LLMCurriculumProvider(llm)
    with pytest.raises(ValueError):
        await provider.get_skill_curriculum("c++")


def test_factory_returns_hardcoded_when_flag_off():
    provider = get_curriculum_provider(_fake_hardcoded, llm_client=FakeLLM(), use_llm=False)
    assert isinstance(provider, HardcodedCurriculumProvider)


def test_factory_returns_llm_when_flag_on_and_client_present():
    provider = get_curriculum_provider(_fake_hardcoded, llm_client=FakeLLM(), use_llm=True)
    assert isinstance(provider, LLMCurriculumProvider)


def test_factory_falls_back_to_hardcoded_when_flag_on_but_no_client():
    provider = get_curriculum_provider(_fake_hardcoded, llm_client=None, use_llm=True)
    assert isinstance(provider, HardcodedCurriculumProvider)

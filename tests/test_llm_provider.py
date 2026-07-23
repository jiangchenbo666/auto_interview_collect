from __future__ import annotations

from src.llm.provider import has_llm_config


def test_has_llm_config_returns_false_without_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert has_llm_config("deepseek") is False
    assert has_llm_config("openai") is False

from __future__ import annotations

from src.llm import provider


def test_has_llm_config_returns_false_without_key(monkeypatch):
    monkeypatch.setattr(provider, "load_env_file", lambda: None)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert provider.has_llm_config("deepseek") is False
    assert provider.has_llm_config("openai") is False

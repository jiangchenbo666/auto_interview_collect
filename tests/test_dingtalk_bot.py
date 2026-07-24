from __future__ import annotations

from src.push.dingtalk_bot import sign_url


def test_sign_url_without_secret_returns_original_url():
    assert sign_url("https://example.com/robot") == "https://example.com/robot"


def test_sign_url_with_secret_adds_signature():
    signed = sign_url("https://example.com/robot?access_token=abc", "secret")

    assert "timestamp=" in signed
    assert "sign=" in signed
    assert signed.startswith("https://example.com/robot?access_token=abc&")

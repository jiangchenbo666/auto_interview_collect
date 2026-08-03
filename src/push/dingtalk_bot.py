from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from src.push.wecom_bot import load_env_file


def send_dingtalk_markdown(
    markdown: str,
    title: str = "Daily Interview Review",
    webhook_url: str | None = None,
    secret: str | None = None,
) -> dict[str, object]:
    """Send one Markdown message through a DingTalk robot webhook."""
    load_env_file()
    webhook = webhook_url or os.getenv("DINGTALK_WEBHOOK_URL")
    if not webhook:
        raise ValueError("Missing DINGTALK_WEBHOOK_URL.")

    signed_url = sign_url(webhook, secret or os.getenv("DINGTALK_SECRET"))
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": markdown,
        },
    }
    request = urllib.request.Request(
        signed_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
    result = json.loads(body)
    if int(result.get("errcode", -1)) != 0:
        raise RuntimeError(f"DingTalk push failed: {result}")
    return result


def sign_url(webhook: str, secret: str | None = None) -> str:
    """Append DingTalk timestamp/sign query parameters when signing is enabled."""
    if not secret:
        return webhook

    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def read_markdown_file(path: str | Path) -> str:
    """Read the generated daily Markdown as UTF-8 text."""
    return Path(path).read_text(encoding="utf-8")

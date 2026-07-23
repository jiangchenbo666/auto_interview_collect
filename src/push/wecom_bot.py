from __future__ import annotations

import json
import os
import urllib.request


def load_env_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs into environment variables."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def send_markdown(markdown: str, webhook_url: str | None = None) -> dict[str, object]:
    """Send a markdown message to a WeCom group robot webhook."""
    webhook = webhook_url or os.getenv("WECOM_WEBHOOK_URL")
    if not webhook:
        raise ValueError("Missing WECOM_WEBHOOK_URL. Put it in .env or pass webhook_url.")

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown,
        },
    }
    request = urllib.request.Request(
        webhook,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)

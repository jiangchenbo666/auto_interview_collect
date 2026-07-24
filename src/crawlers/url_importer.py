from __future__ import annotations

import re
import urllib.request
from html import unescape


def fetch_url_text(url: str) -> str:
    """Fetch one public URL and return rough readable text."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 auto_interview_collect/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
    encoding = guess_encoding(content_type)
    text = raw.decode(encoding, errors="ignore")
    if looks_like_html(text):
        return html_to_text(text)
    return text


def guess_encoding(content_type: str) -> str:
    match = re.search(r"charset=([\w-]+)", content_type, flags=re.I)
    return match.group(1) if match else "utf-8"


def looks_like_html(text: str) -> bool:
    return "<html" in text[:500].lower() or "<body" in text[:1000].lower()


def html_to_text(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", "\n", html)
    html = unescape(html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()

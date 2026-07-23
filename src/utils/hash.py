from __future__ import annotations

import hashlib
import re


def normalize_for_hash(text: str) -> str:
    """Normalize question text so minor punctuation differences deduplicate."""
    normalized = re.sub(r"\s+", "", text.strip().lower())
    normalized = re.sub(r"[？?。.!！:：；;,，、\-\s]+", "", normalized)
    return normalized


def question_hash(question: str) -> str:
    """Return a stable SHA-256 hash for one normalized question."""
    return hashlib.sha256(normalize_for_hash(question).encode("utf-8")).hexdigest()

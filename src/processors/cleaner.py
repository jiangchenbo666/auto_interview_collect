from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize raw markdown/html-ish interview notes before extraction."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_question(question: str) -> str:
    """Remove common markdown/list prefixes from a question line."""
    question = question.strip()
    question = re.sub(r"^\s*[-*+]\s+", "", question)
    question = re.sub(r"^\s*\d+[.)、]\s*", "", question)
    question = re.sub(r"^\s*#{1,6}\s*", "", question)
    question = re.sub(r"^\s*(Q|q)\d*[:：]\s*", "", question)
    question = re.sub(r"\s+", " ", question)
    return question.strip(" -_*`")

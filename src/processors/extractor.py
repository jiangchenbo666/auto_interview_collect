from __future__ import annotations

import re

from src.processors.cleaner import clean_text, normalize_question


# Patterns for common note styles:
# 1. xxx / - xxx / ## xxx / Q: xxx
QUESTION_PATTERNS = [
    re.compile(r"^\s*(?:\d+[.)、]|[-*+]|#{1,6})\s*(.+)$"),
    re.compile(r"^\s*(?:Q|q)\d*[:：]\s*(.+)$"),
]

QUESTION_KEYWORDS = (
    "什么",
    "为什么",
    "如何",
    "怎么",
    "怎样",
    "区别",
    "原理",
    "流程",
    "设计",
    "定位",
    "测试",
    "解释",
)


def looks_like_question(line: str) -> bool:
    """Heuristic filter for lines that are likely interview questions."""
    stripped = line.strip()
    if len(stripped) < 4 or len(stripped) > 120:
        return False
    if stripped.endswith(("?", "？")):
        return True
    return any(keyword in stripped for keyword in QUESTION_KEYWORDS)


def extract_questions(text: str) -> list[str]:
    """Extract question candidates from a markdown/txt interview note."""
    cleaned = clean_text(text)
    questions: list[str] = []

    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue

        matched = None
        for pattern in QUESTION_PATTERNS:
            match = pattern.match(line)
            if match:
                matched = match.group(1)
                break

        candidate = normalize_question(matched or line)
        if looks_like_question(candidate):
            questions.append(candidate)

    return deduplicate_preserve_order(questions)


def deduplicate_preserve_order(items: list[str]) -> list[str]:
    """Remove duplicates while keeping the original reading order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower().replace(" ", "")
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

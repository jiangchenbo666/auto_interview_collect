from __future__ import annotations

import re

from src.processors.cleaner import clean_text, normalize_question


# Patterns for common note styles:
# 1. xxx / - xxx / ## xxx / Q: xxx
QUESTION_PATTERNS = [
    re.compile(r"^\s*(?:\d+[.)、]|[-*+]|#{1,6})\s*(.+)$"),
    re.compile(r"^\s*(?:Q|q)\d*[:：]\s*(.+)$"),
    re.compile(r"^\s*问[：:\s]*(.+)$"),
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
    "解释",
    "压力测试",
    "测试流程",
    "压测",
    "接口测试",
    "自动化",
    "性能测试",
    "冒烟测试",
    "回归测试",
)

NOISE_TITLE_KEYWORDS = (
    "面试题全攻略",
    "面试题",
    "训练营",
    "小林coding",
    "小林测试",
    "面试篇",
    "硬核考察",
    "地基不牢",
    "校招",
    "社招",
    "牛客网",
    "AI 工程",
    "八股",
)


def looks_like_question(line: str) -> bool:
    """Heuristic filter for lines that are likely interview questions."""
    stripped = line.strip()
    if len(stripped) < 4 or len(stripped) > 120:
        return False
    if stripped.startswith("问") and len(stripped) <= 80:
        return True
    if is_noise_question(stripped):
        return False
    if stripped.endswith(("?", "？")):
        return True
    return has_question_marker(stripped)


def is_noise_question(line: str) -> bool:
    """Return True for page titles/navigation headings, not real questions."""
    stripped = line.strip()
    if is_source_label_line(stripped):
        return True
    if "下面我" in stripped or "一个一个说" in stripped:
        return True
    if len(stripped) <= 8 and not stripped.endswith(("?", "？")):
        strong_markers = ("什么", "如何", "怎么", "为什么", "区别")
        return not any(marker in stripped for marker in strong_markers)
    if len(stripped) > 60 and not stripped.endswith(("?", "？")):
        return True
    if not has_question_marker(stripped) and not stripped.endswith(("?", "？")):
        return True
    if any(keyword in stripped for keyword in NOISE_TITLE_KEYWORDS):
        return True
    if "｜" in stripped and "？" not in stripped and "?" not in stripped:
        return True
    if stripped.endswith(("篇", "章", "目录")) and "？" not in stripped:
        return True
    return False


def is_source_label_line(line: str) -> bool:
    """Ignore file/source labels such as 牛客网-字节一面."""
    stripped = line.strip().lstrip("#").strip()
    lowered = stripped.lower()
    answer_prefixes = (
        "正确答案",
        "解题思路",
        "解答思路",
        "深度知识讲解",
        "伪代码示例",
        "踩一下",
    )
    if stripped.startswith(answer_prefixes):
        return True
    return (
        stripped == "牛客网"
        or stripped.startswith("牛客网-")
        or lowered == "ai"
        or lowered.startswith("ai-")
        or stripped.startswith("AI 工程")
        or stripped.startswith(("八股-", "数据库-", "Linux-", "TCP-", "Docker-"))
    )


def has_question_marker(line: str) -> bool:
    """Return True when the line contains a real question-like marker."""
    return any(keyword in line for keyword in QUESTION_KEYWORDS)


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

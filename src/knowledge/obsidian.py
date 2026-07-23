from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_VAULT_PATH = "data/obsidian"
MAX_CHUNK_CHARS = 900


@dataclass(frozen=True)
class KnowledgeSnippet:
    """A small relevant paragraph/chunk retrieved from an Obsidian note."""

    title: str
    path: str
    text: str
    score: int


def retrieve_relevant_snippets(
    query: str,
    vault_path: str | Path = DEFAULT_VAULT_PATH,
    limit: int = 3,
) -> list[KnowledgeSnippet]:
    """Find Obsidian note chunks that overlap with the interview question."""
    root = Path(vault_path)
    if not root.exists():
        return []

    query_terms = tokenize(query)
    if not query_terms:
        return []

    candidates: list[KnowledgeSnippet] = []
    for note_path in root.rglob("*.md"):
        text = read_note(note_path)
        if not text:
            continue
        title = extract_title(note_path, text)
        for chunk in chunk_markdown(text):
            score = score_chunk(query_terms, chunk)
            if score > 0:
                candidates.append(
                    KnowledgeSnippet(
                        title=title,
                        path=str(note_path),
                        text=chunk.strip(),
                        score=score,
                    )
                )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:limit]


def format_snippets(snippets: list[KnowledgeSnippet]) -> str:
    """Format retrieved snippets for prompt/context injection."""
    if not snippets:
        return "暂无匹配的 Obsidian 项目笔记。"
    blocks = []
    for index, item in enumerate(snippets, 1):
        blocks.append(
            f"[{index}] {item.title}\n来源：{item.path}\n内容：{compact_text(item.text)}"
        )
    return "\n\n".join(blocks)


def read_note(path: Path) -> str:
    """Read a markdown note using common Windows/UTF-8 encodings."""
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_title(path: Path, text: str) -> str:
    """Use the first H1 as note title, falling back to the file name."""
    for line in text.splitlines():
        if line.startswith("# "):
            return line.lstrip("# ").strip() or path.stem
    return path.stem


def chunk_markdown(text: str) -> list[str]:
    """Split a note into chunks around headings and blank lines."""
    text = strip_frontmatter(text)
    sections = re.split(r"\n(?=#{1,6}\s+)", text)
    chunks: list[str] = []
    for section in sections:
        paragraphs = re.split(r"\n\s*\n", section)
        buffer = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(buffer) + len(paragraph) > MAX_CHUNK_CHARS and buffer:
                chunks.append(buffer)
                buffer = paragraph
            else:
                buffer = f"{buffer}\n\n{paragraph}".strip()
        if buffer:
            chunks.append(buffer)
    return chunks


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from Obsidian notes."""
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, flags=re.S)


def tokenize(text: str) -> set[str]:
    """Extract simple Chinese/English tokens for lightweight retrieval."""
    lowered = text.lower()
    english = re.findall(r"[a-zA-Z][a-zA-Z0-9_+\-#/]{1,}", lowered)
    chinese = re.findall(r"[\u4e00-\u9fff]{2,}", lowered)
    terms = set(english + chinese)

    # Add short domain keywords because Chinese text often has no spaces.
    domain_terms = (
        "接口",
        "测试",
        "自动化",
        "安全",
        "漏洞",
        "注入",
        "权限",
        "越权",
        "性能",
        "压测",
        "数据库",
        "索引",
        "日志",
        "项目",
        "实习",
    )
    terms.update(term for term in domain_terms if term in lowered)
    return terms


def score_chunk(query_terms: set[str], chunk: str) -> int:
    """Score one chunk by keyword overlap with a small title/heading bonus."""
    lowered = chunk.lower()
    score = 0
    for term in query_terms:
        if term in lowered:
            score += 3 if len(term) >= 4 else 1
    if any(marker in lowered for marker in ("项目", "实习", "负责", "落地", "优化", "修复")):
        score += 2
    return score


def compact_text(text: str, max_chars: int = 650) -> str:
    """Collapse whitespace and keep snippets short enough for prompts."""
    compacted = re.sub(r"\s+", " ", text).strip()
    if len(compacted) <= max_chars:
        return compacted
    return compacted[:max_chars].rstrip() + "..."

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.processors.extractor import extract_questions


SUPPORTED_INBOX_SUFFIXES = {".md", ".txt"}


@dataclass(frozen=True)
class InboxNormalizeResult:
    """Summary for one inbox normalization run."""

    scanned: int
    written: int
    skipped: int
    output_dir: str


def normalize_inbox_files(
    inbox_dirs: list[str | Path],
    output_dir: str | Path,
    overwrite: bool = False,
) -> InboxNormalizeResult:
    """Convert pasted raw interview notes into normalized markdown files."""
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    scanned = 0
    written = 0
    skipped = 0
    for inbox_dir in inbox_dirs:
        root = Path(inbox_dir)
        if not root.exists():
            continue
        for source_path in iter_inbox_files(root):
            scanned += 1
            text = read_text(source_path)
            if not text.strip():
                skipped += 1
                continue
            normalized = build_normalized_markdown(source_path, text)
            output_path = output_root / normalized_filename(source_path, text)
            if output_path.exists() and not overwrite:
                skipped += 1
                continue
            output_path.write_text(normalized, encoding="utf-8")
            written += 1

    return InboxNormalizeResult(
        scanned=scanned,
        written=written,
        skipped=skipped,
        output_dir=str(output_root),
    )


def iter_inbox_files(root: Path) -> list[Path]:
    """Return supported pasted-note files in stable order."""
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_INBOX_SUFFIXES
    )


def build_normalized_markdown(source_path: Path, text: str) -> str:
    """Build a normalized markdown note with extracted questions first."""
    title = title_from_text(source_path, text)
    source_url = extract_source_url(text)
    questions = extract_questions(text)
    lines = [
        f"# {title}",
        "",
        f"- 原始文件：{source_path}",
        f"- 整理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if source_url:
        lines.append(f"- 来源链接：{source_url}")
    lines.extend(["", "## 抽取题目", ""])
    if questions:
        lines.extend(f"{index}. {question}" for index, question in enumerate(questions, 1))
    else:
        lines.append("- 暂未自动识别到明确问题，请手动补充问题列表。")
    lines.extend(["", "## 原始材料", "", text.strip(), ""])
    return "\n".join(lines)


def normalized_filename(source_path: Path, text: str) -> str:
    """Create a stable output filename to avoid repeated OCR/import cost."""
    digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:10]
    stem = safe_stem(source_path.stem)
    return f"{stem}-{digest}.md"


def safe_stem(stem: str) -> str:
    """Keep filenames readable while removing awkward shell/path characters."""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", stem, flags=re.U).strip("-._")
    return cleaned[:60] or "interview-note"


def title_from_text(source_path: Path, text: str) -> str:
    """Use the first markdown heading when present, otherwise the file stem."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("# ").strip() or source_path.stem
    return source_path.stem


def extract_source_url(text: str) -> str | None:
    """Find the first URL in a pasted note."""
    match = re.search(r"https?://\S+", text)
    if not match:
        return None
    return match.group(0).rstrip(").,，。")


def read_text(path: Path) -> str:
    """Read pasted notes with common encodings."""
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")

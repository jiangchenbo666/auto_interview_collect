from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.processors.extractor import extract_questions


SUPPORTED_TEXT_SUFFIXES = {".md", ".txt"}
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
SUPPORTED_INBOX_SUFFIXES = SUPPORTED_TEXT_SUFFIXES | SUPPORTED_IMAGE_SUFFIXES


@dataclass(frozen=True)
class InboxNormalizeResult:
    """Summary for one inbox normalization run."""

    scanned: int
    written: int
    skipped: int
    output_dir: str
    images_parsed: int = 0
    images_pending: int = 0
    errors: tuple[str, ...] = ()


def normalize_inbox_files(
    inbox_dirs: list[str | Path],
    output_dir: str | Path,
    overwrite: bool = False,
    use_vision: bool = False,
) -> InboxNormalizeResult:
    """Convert pasted notes/screenshots into normalized markdown files."""
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    scanned = 0
    written = 0
    skipped = 0
    images_parsed = 0
    images_pending = 0
    errors: list[str] = []
    for inbox_dir in inbox_dirs:
        root = Path(inbox_dir)
        if not root.exists():
            continue
        for source_path in iter_inbox_files(root):
            scanned += 1
            if source_path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES:
                print(f"[inbox] normalize text {source_path}", flush=True)
                text = read_text(source_path)
                if not text.strip():
                    skipped += 1
                    continue
                output_path = output_root / normalized_filename(source_path, text)
                if output_path.exists() and not overwrite:
                    skipped += 1
                    continue
                normalized = build_normalized_markdown(source_path, text)
            else:
                digest = file_digest(source_path)
                output_path = output_root / normalized_filename(source_path, digest)
                if output_path.exists() and not overwrite:
                    skipped += 1
                    continue
                print(f"[inbox] parse image {source_path}", flush=True)
                normalized, parsed, error = build_image_markdown(source_path, use_vision=use_vision)
                if parsed:
                    images_parsed += 1
                else:
                    images_pending += 1
                if error:
                    errors.append(f"{source_path}: {error}")
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
        images_parsed=images_parsed,
        images_pending=images_pending,
        errors=tuple(errors),
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
    label = source_label_from_filename(source_path)
    source_url = extract_source_url(text)
    questions = extract_questions(text)
    lines = [
        f"# {title}",
        "",
        f"- 原始文件：{source_path}",
        f"- 整理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if label:
        lines.append(f"- 资料标签：{label}")
    if source_url:
        lines.append(f"- 来源链接：{source_url}")
    lines.extend(["", "## 抽取题目", ""])
    if questions:
        lines.extend(f"{index}. {question}" for index, question in enumerate(questions, 1))
    else:
        lines.append("- 暂未自动识别到明确问题，请手动补充问题列表。")
    lines.extend(["", "## 原始材料", "", text.strip(), ""])
    return "\n".join(lines)


def build_image_markdown(source_path: Path, use_vision: bool = False) -> tuple[str, bool, str | None]:
    """Convert one screenshot into markdown, using Kimi vision when enabled."""
    if not use_vision:
        return build_pending_image_markdown(source_path, "未启用视觉模型，本次只登记截图。"), False, None

    try:
        from src.llm.provider import extract_interview_material_from_image

        extracted = extract_interview_material_from_image(source_path).strip()
    except Exception as exc:  # noqa: BLE001
        reason = str(exc)
        return build_pending_image_markdown(source_path, f"视觉解析失败：{reason}"), False, reason

    if not extracted:
        return build_pending_image_markdown(source_path, "视觉模型未返回可用文本。"), False, "empty vision response"

    markdown = build_normalized_markdown(source_path, extracted)
    return markdown, True, None


def build_pending_image_markdown(source_path: Path, reason: str) -> str:
    """Create a source card for screenshots that still need OCR/vision parsing."""
    lines = [
        f"# 截图待解析 - {source_path.stem}",
        "",
        f"- 原始文件：{source_path}",
        f"- 整理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 资料类型：截图",
        f"- 处理状态：{reason}",
        "",
        "## 抽取题目",
        "",
        "- 暂未自动识别到明确题目；启用 Kimi 视觉模型后会在流水线中解析。",
        "",
        "## 原始材料",
        "",
        f"图片文件：{source_path}",
        "",
    ]
    return "\n".join(lines)


def normalized_filename(source_path: Path, text: str) -> str:
    """Create a stable output filename to avoid repeated OCR/import cost."""
    digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:10]
    stem = safe_stem(source_path.stem)
    return f"{stem}-{digest}.md"


def file_digest(path: Path) -> str:
    """Return a stable content hash for binary inbox files."""
    return hashlib.sha1(path.read_bytes()).hexdigest()[:10]


def safe_stem(stem: str) -> str:
    """Keep filenames readable while removing awkward shell/path characters."""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", stem, flags=re.U).strip("-._")
    return cleaned[:60] or "interview-note"


def title_from_text(source_path: Path, text: str) -> str:
    """Use the first markdown heading when present, otherwise the file stem."""
    label = source_label_from_filename(source_path)
    if label:
        return label
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("# ").strip() or source_path.stem
    return source_path.stem


def source_label_from_filename(path: Path) -> str | None:
    """Read source labels from filenames like 牛客网-字节一面.md or ai-RAG.md."""
    stem = path.stem.strip()
    lower = stem.lower()
    if stem.startswith("牛客网"):
        return stem
    if lower == "ai":
        return "AI 工程"
    if lower.startswith("ai-") or lower.startswith("ai_"):
        return "AI 工程-" + stem[3:].strip("-_ ")
    if stem.startswith(("八股", "数据库", "Linux", "TCP", "Docker")):
        return stem
    return None


def source_type_from_filename(path: Path, default: str = "real_interview") -> str:
    """Map filename labels to source_type for queue mixing and display."""
    label = source_label_from_filename(path)
    if not label:
        return default
    if label.startswith("牛客网"):
        return "nowcoder"
    if label.startswith("AI 工程"):
        return "ai_engineering"
    if label.startswith(("八股", "数据库", "Linux", "TCP", "Docker")):
        return "foundation_bagu"
    return default


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

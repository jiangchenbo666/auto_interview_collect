from __future__ import annotations

from src.processors.inbox_normalizer import normalize_inbox_files, source_label_from_filename, source_type_from_filename


def test_normalize_inbox_files_writes_markdown(tmp_path):
    inbox = tmp_path / "inbox"
    output = tmp_path / "normalized"
    inbox.mkdir()
    source = inbox / "nowcoder-ai.txt"
    source.write_text(
        """
来源：https://www.nowcoder.com/discuss/123

1. Harness 有了解吗？用它做什么？
2. 什么是 MVP？你的项目怎么定义 MVP？
""",
        encoding="utf-8",
    )

    result = normalize_inbox_files([inbox], output)
    files = list(output.glob("*.md"))

    assert result.scanned == 1
    assert result.written == 1
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "## 抽取题目" in content
    assert "Harness 有了解吗" in content
    assert "https://www.nowcoder.com/discuss/123" in content


def test_normalize_inbox_files_skips_existing_output(tmp_path):
    inbox = tmp_path / "inbox"
    output = tmp_path / "normalized"
    inbox.mkdir()
    source = inbox / "same.txt"
    source.write_text("1. TCP 三次握手为什么不是两次？", encoding="utf-8")

    first = normalize_inbox_files([inbox], output)
    second = normalize_inbox_files([inbox], output)

    assert first.written == 1
    assert second.written == 0
    assert second.skipped == 1


def test_normalize_inbox_files_registers_image_without_vision(tmp_path):
    inbox = tmp_path / "inbox"
    output = tmp_path / "normalized"
    inbox.mkdir()
    screenshot = inbox / "nowcoder-api.png"
    screenshot.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    result = normalize_inbox_files([inbox], output)
    files = list(output.glob("*.md"))

    assert result.scanned == 1
    assert result.written == 1
    assert result.images_pending == 1
    assert result.images_parsed == 0
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "截图待解析" in content
    assert "nowcoder-api.png" in content


def test_filename_source_label_protocol(tmp_path):
    assert source_label_from_filename(tmp_path / "牛客网-字节一面.md") == "牛客网-字节一面"
    assert source_label_from_filename(tmp_path / "牛客网.md") == "牛客网"
    assert source_label_from_filename(tmp_path / "牛客网1.md") == "牛客网1"
    assert source_label_from_filename(tmp_path / "联想测试开发面经.md") == "联想测试开发面经"
    assert source_label_from_filename(tmp_path / "面经资料-未整理" / "随手收藏.md") == "随手收藏"
    assert source_type_from_filename(tmp_path / "牛客网-字节一面.md") == "curated_interview"
    assert source_type_from_filename(tmp_path / "联想测试开发面经.md") == "curated_interview"
    assert source_label_from_filename(tmp_path / "ai-RAG评测.md") == "AI 工程-RAG评测"
    assert source_type_from_filename(tmp_path / "ai-RAG评测.md") == "ai_engineering"

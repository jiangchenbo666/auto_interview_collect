from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

"""Command line entrypoint.

你平时运行的命令都从这里进入：
- init: 初始化 SQLite
- import-file: 导入 md/txt 面经
- process: 分类并生成答案
- daily: 生成/发送今日复习内容
- serve-daily: 常驻定时推送
- list/export-md: 查看和导出题库
"""

from src.config_loader import get_db_path, get_obsidian_vault_path
from src.crawlers.url_importer import fetch_url_text
from src.knowledge.obsidian import retrieve_relevant_snippets
from src.processors.extractor import extract_questions, is_noise_question
from src.processors.inbox_normalizer import normalize_inbox_files
from src.scheduler.daily_job import get_review_questions_for_today, rebuild_answers, process_pending_questions, run_daily_loop, run_daily_push
from src.storage.db import init_db
from src.storage import repository
from src.push.dingtalk_bot import read_markdown_file, send_dingtalk_markdown
from src.viewer.html_builder import build_today_html


DEFAULT_TODAY_OUTPUT = "data/exports/today.md"
DEFAULT_TODAY_HTML_OUTPUT = "data/exports/today.html"
DEFAULT_BANK_OUTPUT = "data/exports/questions.md"
DEFAULT_SOURCES_CONFIG = "config/real_sources.yaml"
DEFAULT_REAL_INTERVIEWS_DIR = "data/raw/real_interviews"
DEFAULT_INBOX_DIR = "data/raw/inbox"
DEFAULT_OBSIDIAN_INBOX_DIR = "data/obsidian/面经资料/待整理"
DEFAULT_OBSIDIAN_UNSORTED_INBOX_DIR = "data/obsidian/面经资料-未整理"
DEFAULT_OBSIDIAN_INBOX_DIRS = [
    DEFAULT_OBSIDIAN_INBOX_DIR,
    DEFAULT_OBSIDIAN_UNSORTED_INBOX_DIR,
]
DEFAULT_NORMALIZED_INBOX_DIR = "data/raw/real_interviews/nowcoder"


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize local database."""
    init_db(args.db)
    print(f"Initialized database: {args.db}")


def cmd_import_file(args: argparse.Namespace) -> None:
    """Read a local md/txt file, extract questions, and store them."""
    init_db(args.db)
    path = Path(args.path)
    result, extracted = import_one_file(args.db, path, source_type=args.source_type)
    print(f"Extracted {extracted} questions.")
    print(f"Accepted {result['accepted']}, skipped {result['skipped']}.")


def cmd_import_folder(args: argparse.Namespace) -> None:
    """Import all md/txt files in a folder as real interview material."""
    init_db(args.db)
    root = Path(args.path)
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    files = [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    ]
    total_extracted = 0
    total_accepted = 0
    total_skipped = 0
    for path in files:
        result, extracted = import_one_file(args.db, path, source_type=args.source_type)
        total_extracted += extracted
        total_accepted += result["accepted"]
        total_skipped += result["skipped"]

    print(f"Files scanned: {len(files)}")
    print(f"Extracted {total_extracted} questions.")
    print(f"Accepted {total_accepted}, skipped {total_skipped}.")


def cmd_normalize_inbox(args: argparse.Namespace) -> None:
    """Convert pasted raw notes into normalized markdown interview files."""
    result = normalize_inbox_files(
        [Path(path) for path in args.inbox],
        args.output,
        overwrite=args.overwrite,
        use_vision=args.use_vision,
    )
    print(f"Inbox files scanned: {result.scanned}")
    print(f"Normalized markdown written: {result.written}")
    print(f"Skipped: {result.skipped}")
    print(f"Images parsed: {result.images_parsed}")
    print(f"Images pending: {result.images_pending}")
    for error in result.errors:
        print(f"[image warning] {error}")
    print(f"Output folder: {result.output_dir}")


def cmd_import_url(args: argparse.Namespace) -> None:
    """Fetch one public URL and import extracted questions."""
    init_db(args.db)
    text = fetch_url_text(args.url)
    questions = extract_questions(text)
    result = repository.bulk_insert_questions(
        args.db,
        questions,
        source_url=args.url,
        source_type=args.source_type,
    )
    print(f"URL: {args.url}")
    print(f"Extracted {len(questions)} questions.")
    print(f"Accepted {result['accepted']}, skipped {result['skipped']}.")


def cmd_refresh_sources(args: argparse.Namespace) -> None:
    """Fetch configured public sources and import real questions."""
    init_db(args.db)
    sources = load_public_sources(args.config)
    total_extracted = 0
    total_accepted = 0
    total_skipped = 0
    failed: list[tuple[str, str]] = []

    for source in sources:
        name = source.get("name") or source["url"]
        try:
            text = fetch_url_text(source["url"])
            questions = extract_questions(text)
            result = repository.bulk_insert_questions(
                args.db,
                questions,
                source_url=source["url"],
                source_type=source.get("type", "public_url"),
            )
            total_extracted += len(questions)
            total_accepted += result["accepted"]
            total_skipped += result["skipped"]
            print(f"[ok] {name}: extracted={len(questions)} accepted={result['accepted']} skipped={result['skipped']}")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, str(exc)))
            print(f"[failed] {name}: {exc}")

    print(f"Sources enabled: {len(sources)}")
    print(f"Extracted {total_extracted} questions.")
    print(f"Accepted {total_accepted}, skipped {total_skipped}.")
    if failed:
        print("Failed sources:")
        for name, reason in failed:
            print(f"- {name}: {reason}")


def import_one_file(db_path: str, path: Path, source_type: str = "real_interview") -> tuple[dict[str, int], int]:
    """Extract and store questions from one source file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    questions = extract_questions(text)
    result = repository.bulk_insert_questions(
        db_path,
        questions,
        source_url=str(path),
        source_type=source_type,
    )
    return result, len(questions)


def cmd_process(args: argparse.Namespace) -> None:
    """Run classification and answer generation for pending questions."""
    init_db(args.db)
    count = process_pending_questions(
        args.db,
        vault_path=args.vault,
        limit=args.limit,
        use_llm=args.use_llm,
    )
    print(f"Processed {count} question state transitions.")


def cmd_rebuild_answers(args: argparse.Namespace) -> None:
    """Regenerate existing answers with latest profile and Obsidian notes."""
    init_db(args.db)
    count = rebuild_answers(
        args.db,
        vault_path=args.vault,
        limit=args.limit,
        use_llm=args.use_llm,
    )
    print(f"Rebuilt {count} answers.")


def cmd_vault_status(args: argparse.Namespace) -> None:
    """Show whether Obsidian markdown notes can be detected."""
    root = Path(args.vault)
    files = list(root.rglob("*.md")) if root.exists() else []
    print(f"Obsidian vault path: {root}")
    print(f"Markdown notes found: {len(files)}")
    if args.query:
        snippets = retrieve_relevant_snippets(args.query, vault_path=root, limit=args.limit)
        print(f"Relevant snippets for: {args.query}")
        for item in snippets:
            print(f"- {item.title} | score={item.score} | {item.path}")


def cmd_cleanup_noise(args: argparse.Namespace) -> None:
    """Mark obvious page titles/navigation headings as ignored."""
    init_db(args.db)
    rows = repository.export_questions(args.db)
    changed = 0
    for row in rows:
        if row.get("status") != "ignored" and is_noise_question(row["question"]):
            repository.mark_ignored(args.db, row["id"])
            changed += 1
    print(f"Ignored noisy rows: {changed}")


def cmd_push_dingtalk(args: argparse.Namespace) -> None:
    """Send a generated markdown review to DingTalk."""
    markdown = read_markdown_file(args.markdown)
    if args.page_url:
        markdown = prepend_page_link(markdown, args.page_url)
    result = send_dingtalk_markdown(markdown, title=args.title)
    print(result)


def cmd_daily(args: argparse.Namespace) -> None:
    """Build today's review markdown; send it unless dry-run is enabled."""
    init_db(args.db)
    mode, questions = get_review_questions_for_today(args.db, limit=args.limit)
    markdown = build_daily_markdown_for_mode(mode, questions)
    if args.output:
        write_text_file(args.output, markdown)
        print(f"Saved daily review to {args.output}\n")
    if args.html_output:
        html_questions = attach_obsidian_evidence(questions, args.vault)
        write_text_file(args.html_output, build_today_html(html_questions, mode=mode))
        print(f"Saved HTML review to {args.html_output}\n")
        if args.open:
            open_in_browser(args.html_output)
    print(markdown)
    if args.mark_reviewed:
        repository.mark_questions_pushed(args.db, [item["id"] for item in questions])
        print("\nMarked today's questions as reviewed.")
    if args.dry_run:
        print("\nDry run only. Nothing was sent.")


def cmd_study(args: argparse.Namespace) -> None:
    """Daily one-command workflow for real study."""
    init_db(args.db)
    if args.refresh_sources:
        refresh_args = argparse.Namespace(
            db=args.db,
            config=args.sources_config,
        )
        cmd_refresh_sources(refresh_args)
    if args.normalize_inbox:
        use_vision = getattr(args, "vision_inbox", None)
        if use_vision is None:
            use_vision = args.use_llm
        result = normalize_inbox_files(
            [args.inbox_dir, *as_path_list(args.obsidian_inbox_dir)],
            args.normalized_inbox_dir,
            overwrite=args.overwrite_inbox,
            use_vision=use_vision,
        )
        print(
            "Inbox normalized: "
            f"scanned={result.scanned} written={result.written} skipped={result.skipped} "
            f"images_parsed={result.images_parsed} images_pending={result.images_pending}"
        )
        for error in result.errors:
            print(f"[image warning] {error}")
    if args.import_local:
        local_root = Path(args.real_dir)
        if local_root.exists():
            import_args = argparse.Namespace(
                db=args.db,
                path=str(local_root),
                source_type="real_interview",
            )
            cmd_import_folder(import_args)

    changed = process_pending_questions(
        args.db,
        vault_path=args.vault,
        limit=args.process_limit,
        use_llm=args.use_llm,
    )
    mode, questions = get_review_questions_for_today(args.db, limit=args.limit)
    remaining_after_today = max(
        0,
        repository.count_unreviewed_ready_questions(args.db) - len(questions),
    )
    markdown = build_daily_markdown_for_mode(mode, questions)
    markdown = append_inventory_notice(
        markdown,
        shown_count=len(questions),
        requested_count=args.limit,
        remaining_after_today=remaining_after_today,
        low_inventory_threshold=args.low_inventory_threshold,
    )
    write_text_file(args.today_output, markdown)
    html_questions = attach_obsidian_evidence(questions, args.vault)
    write_text_file(args.html_output, build_today_html(html_questions, mode=mode))
    write_text_file(args.bank_output, build_question_bank_markdown(repository.export_questions(args.db)))

    if args.mark_reviewed:
        repository.mark_questions_pushed(args.db, [item["id"] for item in questions])

    print("Study page generated.")
    print(f"Mode: {mode}")
    print(f"Processed state transitions: {changed}")
    print(f"Questions shown: {len(questions)}")
    print(f"Unreviewed ready after today: {remaining_after_today}")
    for item in questions:
        print(f"- [{item['id']}] {item['question']}")
    print(f"Today's HTML page: {args.html_output}")
    print(f"Marked reviewed: {args.mark_reviewed}")
    if args.open:
        open_in_browser(args.html_output)
        print("Opened today's HTML page in your browser.")


def cmd_serve_daily(args: argparse.Namespace) -> None:
    """Run a simple foreground daily scheduler."""
    init_db(args.db)
    print(f"Daily scheduler started. time={args.time}, limit={args.limit}, dry_run={args.dry_run}")
    run_daily_loop(
        args.db,
        push_time=args.time,
        limit=args.limit,
        dry_run=args.dry_run,
        use_llm=args.use_llm,
        vault_path=args.vault,
    )


def cmd_list(args: argparse.Namespace) -> None:
    """Print questions for quick terminal inspection."""
    init_db(args.db)
    if args.status:
        rows = repository.get_questions_by_status(args.db, args.status, args.limit)
    else:
        rows = repository.list_questions(args.db, args.limit)
    for row in rows:
        print(f"[{row['id']}] {row['status']} | {row.get('category') or '-'} | {row['question']}")


def cmd_export_md(args: argparse.Namespace) -> None:
    """Export the whole question bank as a markdown document."""
    init_db(args.db)
    rows = repository.export_questions(args.db)
    write_text_file(args.output, build_question_bank_markdown(rows))
    print(f"Exported {len(rows)} questions to {args.output}")


def cmd_demo(args: argparse.Namespace) -> None:
    """One-command local demo: init -> import sample -> process -> export -> open."""
    init_db(args.db)
    sample_path = Path("data/raw/sample_questions.md")
    questions = extract_questions(sample_path.read_text(encoding="utf-8"))
    result = repository.bulk_insert_questions(
        args.db,
        questions,
        source_url=str(sample_path),
        source_type="file",
    )
    changed = process_pending_questions(
        args.db,
        vault_path=args.vault,
        limit=args.process_limit,
        use_llm=args.use_llm,
    )
    mode, today_questions = get_review_questions_for_today(args.db, args.limit)
    daily_markdown = build_daily_markdown_for_mode(mode, today_questions)
    rows = repository.export_questions(args.db)

    write_text_file(args.today_output, daily_markdown)
    html_questions = attach_obsidian_evidence(today_questions, args.vault)
    write_text_file(args.html_output, build_today_html(html_questions, mode=mode))
    write_text_file(args.bank_output, build_question_bank_markdown(rows))

    print("Demo completed.")
    print(f"Imported sample questions: accepted={result['accepted']}, skipped={result['skipped']}")
    print(f"Processed state transitions: {changed}")
    print(f"Today's review: {args.today_output}")
    print(f"Today's HTML page: {args.html_output}")
    print(f"Question bank export: {args.bank_output}")
    print(f"Obsidian vault: {args.vault}")
    print("Answer mode: configured LLM API" if args.use_llm else "Answer mode: local templates + Obsidian context")
    if args.open:
        open_in_browser(args.html_output)
        print("Opened today's HTML page in your browser.")


def write_text_file(path: str | Path, text: str) -> None:
    """Write UTF-8 text and create parent folders when needed."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def as_path_list(value: str | Path | list[str | Path] | tuple[str | Path, ...]) -> list[str | Path]:
    """Normalize argparse single/repeated path values into a list."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def open_in_browser(path: str | Path) -> None:
    """Open a local file in the default browser."""
    webbrowser.open(Path(path).resolve().as_uri())


def prepend_page_link(markdown: str, page_url: str) -> str:
    """Add the GitHub Pages study entry at the top of a DingTalk message."""
    clean_url = page_url.strip()
    if not clean_url:
        return markdown
    return f"完整复习页：[{clean_url}]({clean_url})\n\n{markdown}"


def append_inventory_notice(
    markdown: str,
    shown_count: int,
    requested_count: int,
    remaining_after_today: int,
    low_inventory_threshold: int,
) -> str:
    """Append a reminder when the review bank is running low."""
    notices = []
    if shown_count < requested_count:
        notices.append(f"今天只凑够 {shown_count}/{requested_count} 道题，需要补充新的面经或八股资料。")
    if remaining_after_today <= low_inventory_threshold:
        notices.append(
            f"题库余量提醒：未复习可推送题约 {remaining_after_today} 道，建议补充牛客面经、项目追问或 AI 工程题。"
        )
    if not notices:
        return markdown
    return f"{markdown}\n\n---\n\n## 资料库提醒\n" + "\n".join(f"- {notice}" for notice in notices)


def attach_obsidian_evidence(
    questions: list[dict],
    vault_path: str | Path,
    limit: int = 3,
) -> list[dict]:
    """Attach matched Obsidian snippets for HTML audit display."""
    enriched = []
    for item in questions:
        copied = dict(item)
        copied["knowledge_evidence"] = [
            {
                "title": snippet.title,
                "path": snippet.path,
                "score": snippet.score,
                "text": snippet.text,
            }
            for snippet in retrieve_relevant_snippets(
                item.get("question") or "",
                vault_path=vault_path,
                limit=limit,
            )
        ]
        enriched.append(copied)
    return enriched


def build_question_bank_markdown(rows: list[dict]) -> str:
    """Render the whole SQLite question bank as a readable Markdown file."""
    lines = ["# 面试题库导出", ""]
    for row in rows:
        lines.extend(
            [
                f"## {row['id']}. {row['question']}",
                "",
                f"- 分类：{row.get('category') or '未分类'}",
                f"- 状态：{row.get('status')}",
                f"- 难度：{row.get('difficulty')}",
                "",
                "### 标准答案",
                row.get("answer") or "待生成",
                "",
                "### 面试表达",
                row.get("project_answer") or "待生成",
                "",
            ]
        )
    return "\n".join(lines)


def build_daily_markdown_for_mode(mode: str, questions: list[dict]) -> str:
    """Build Markdown with a Sunday weekly-review heading when needed."""
    from src.push.markdown_builder import build_daily_markdown

    markdown = build_daily_markdown(questions)
    if mode == "weekly":
        return markdown.replace("# 今日测开面试复习", "# 周日精选复习", 1)
    return markdown


def load_public_sources(path: str | Path) -> list[dict[str, str]]:
    """Load config/real_sources.yaml without adding a YAML dependency."""
    config_path = Path(path)
    if not config_path.exists():
        return []
    sources: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped == "sources:":
            continue
        if stripped.startswith("- "):
            if current:
                sources.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = value.strip()
        elif current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        sources.append(current)
    return [
        source for source in sources
        if source.get("enabled", "true").lower() == "true" and source.get("url")
    ]


def build_parser() -> argparse.ArgumentParser:
    """Define all CLI commands and their arguments."""
    parser = argparse.ArgumentParser(description="测开面经收集与每日推送工具")
    parser.set_defaults(func=None)

    def add_db_argument(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--db", default=get_db_path(), help="SQLite database path")

    init_parser = parser.add_subparsers(dest="command")

    p_init = init_parser.add_parser("init", help="初始化数据库")
    add_db_argument(p_init)
    p_init.set_defaults(func=cmd_init)

    p_import = init_parser.add_parser("import-file", help="从 md/txt 文件导入题目")
    p_import.add_argument("path")
    p_import.add_argument("--source-type", default="real_interview", help="来源类型，例如 nowcoder/github/blog/manual")
    add_db_argument(p_import)
    p_import.set_defaults(func=cmd_import_file)

    p_import_folder = init_parser.add_parser("import-folder", help="批量导入文件夹下的真实 md/txt 面经")
    p_import_folder.add_argument("path")
    p_import_folder.add_argument("--source-type", default="real_interview", help="来源类型，例如 nowcoder/github/blog/manual")
    add_db_argument(p_import_folder)
    p_import_folder.set_defaults(func=cmd_import_folder)

    p_normalize = init_parser.add_parser("normalize-inbox", help="把复制粘贴的原始面经整理成规范 Markdown")
    p_normalize.add_argument(
        "--inbox",
        action="append",
        default=[DEFAULT_INBOX_DIR, *DEFAULT_OBSIDIAN_INBOX_DIRS],
        help="待整理资料目录，可重复传入",
    )
    p_normalize.add_argument("--output", default=DEFAULT_NORMALIZED_INBOX_DIR)
    p_normalize.add_argument("--overwrite", action="store_true")
    p_normalize.add_argument("--use-vision", action="store_true", help="使用 Kimi 视觉模型解析截图")
    p_normalize.set_defaults(func=cmd_normalize_inbox)

    p_import_url = init_parser.add_parser("import-url", help="导入一个公开 URL 中的真实面经/八股题")
    p_import_url.add_argument("url")
    p_import_url.add_argument("--source-type", default="public_url")
    add_db_argument(p_import_url)
    p_import_url.set_defaults(func=cmd_import_url)

    p_refresh = init_parser.add_parser("refresh-sources", help="从 config/real_sources.yaml 刷新公开真实来源")
    p_refresh.add_argument("--config", default=DEFAULT_SOURCES_CONFIG)
    add_db_argument(p_refresh)
    p_refresh.set_defaults(func=cmd_refresh_sources)

    p_process = init_parser.add_parser("process", help="分类并生成答案")
    p_process.add_argument("--limit", type=int, default=20)
    p_process.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    p_process.add_argument("--use-llm", action="store_true", help="使用 .env 中配置的 LLM API 生成答案")
    add_db_argument(p_process)
    p_process.set_defaults(func=cmd_process)

    p_rebuild = init_parser.add_parser("rebuild-answers", help="根据最新项目经历/Obsidian 笔记重写已有答案")
    p_rebuild.add_argument("--limit", type=int, default=50)
    p_rebuild.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    p_rebuild.add_argument("--use-llm", action="store_true", help="使用 .env 中配置的 LLM API 生成答案")
    add_db_argument(p_rebuild)
    p_rebuild.set_defaults(func=cmd_rebuild_answers)

    p_vault = init_parser.add_parser("vault-status", help="检查 Obsidian 知识库是否能被识别")
    p_vault.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    p_vault.add_argument("--query", help="可选：用一个题目测试相关笔记检索")
    p_vault.add_argument("--limit", type=int, default=5)
    p_vault.set_defaults(func=cmd_vault_status)

    p_cleanup = init_parser.add_parser("cleanup-noise", help="清理网页标题/导航等非真实题目噪声")
    add_db_argument(p_cleanup)
    p_cleanup.set_defaults(func=cmd_cleanup_noise)

    p_dingtalk = init_parser.add_parser("push-dingtalk", help="把 Markdown 复习内容推送到钉钉机器人")
    p_dingtalk.add_argument("--markdown", default=DEFAULT_TODAY_OUTPUT)
    p_dingtalk.add_argument("--title", default="今日测开面试复习")
    p_dingtalk.add_argument("--page-url", help="可选：在钉钉消息开头附加 GitHub Pages 学习页链接")
    p_dingtalk.set_defaults(func=cmd_push_dingtalk, title="Daily Interview Review")

    p_daily = init_parser.add_parser("daily", help="生成或推送今日学习内容")
    p_daily.add_argument("--limit", type=int, default=8)
    p_daily.add_argument("--dry-run", action="store_true")
    p_daily.add_argument("--output", help="把今日复习内容保存为 Markdown 文件")
    p_daily.add_argument("--html-output", default=DEFAULT_TODAY_HTML_OUTPUT, help="保存 HTML 复习页面")
    p_daily.add_argument("--open", action=argparse.BooleanOptionalAction, default=True, help="生成后打开浏览器")
    p_daily.add_argument("--mark-reviewed", action="store_true", help="标记今天展示的题，避免明天重复")
    p_daily.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    add_db_argument(p_daily)
    p_daily.set_defaults(func=cmd_daily)

    p_study = init_parser.add_parser("study", help="每日学习：刷新真实来源、处理答案、生成页面、默认标记已复习")
    p_study.add_argument("--limit", type=int, default=8)
    p_study.add_argument("--process-limit", type=int, default=50)
    p_study.add_argument("--low-inventory-threshold", type=int, default=30)
    p_study.add_argument("--sources-config", default=DEFAULT_SOURCES_CONFIG)
    p_study.add_argument("--real-dir", default=DEFAULT_REAL_INTERVIEWS_DIR)
    p_study.add_argument("--normalize-inbox", action=argparse.BooleanOptionalAction, default=True)
    p_study.add_argument("--inbox-dir", default=DEFAULT_INBOX_DIR)
    p_study.add_argument(
        "--obsidian-inbox-dir",
        action="append",
        default=list(DEFAULT_OBSIDIAN_INBOX_DIRS),
        help="Obsidian 待整理资料目录，可重复传入",
    )
    p_study.add_argument("--normalized-inbox-dir", default=DEFAULT_NORMALIZED_INBOX_DIR)
    p_study.add_argument("--overwrite-inbox", action="store_true")
    p_study.add_argument(
        "--vision-inbox",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="是否尝试用多模态模型解析 inbox 截图；默认跟随 --use-llm",
    )
    p_study.add_argument("--today-output", default=DEFAULT_TODAY_OUTPUT)
    p_study.add_argument("--html-output", default=DEFAULT_TODAY_HTML_OUTPUT)
    p_study.add_argument("--bank-output", default=DEFAULT_BANK_OUTPUT)
    p_study.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    p_study.add_argument("--use-llm", action="store_true", help="使用 .env 中配置的 LLM API 生成答案")
    p_study.add_argument("--refresh-sources", action=argparse.BooleanOptionalAction, default=True)
    p_study.add_argument("--import-local", action=argparse.BooleanOptionalAction, default=True)
    p_study.add_argument("--mark-reviewed", action=argparse.BooleanOptionalAction, default=True)
    p_study.add_argument("--open", action=argparse.BooleanOptionalAction, default=True)
    add_db_argument(p_study)
    p_study.set_defaults(func=cmd_study)

    p_serve = init_parser.add_parser("serve-daily", help="常驻进程，每天定时处理并推送")
    p_serve.add_argument("--time", default="08:30", help="每日推送时间，格式 HH:MM")
    p_serve.add_argument("--limit", type=int, default=8)
    p_serve.add_argument("--dry-run", action="store_true")
    p_serve.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    p_serve.add_argument("--use-llm", action="store_true", help="使用 .env 中配置的 LLM API 生成答案")
    add_db_argument(p_serve)
    p_serve.set_defaults(func=cmd_serve_daily)

    p_list = init_parser.add_parser("list", help="查看题目")
    p_list.add_argument("--status")
    p_list.add_argument("--limit", type=int, default=20)
    add_db_argument(p_list)
    p_list.set_defaults(func=cmd_list)

    p_export = init_parser.add_parser("export-md", help="导出 Markdown 题库")
    p_export.add_argument("output")
    add_db_argument(p_export)
    p_export.set_defaults(func=cmd_export_md)

    p_demo = init_parser.add_parser("demo", help="一条命令跑通本地演示并导出 Markdown")
    p_demo.add_argument("--limit", type=int, default=3, help="今日复习题目数量")
    p_demo.add_argument("--process-limit", type=int, default=50, help="本次最多处理多少道待处理题")
    p_demo.add_argument("--today-output", default=DEFAULT_TODAY_OUTPUT)
    p_demo.add_argument("--html-output", default=DEFAULT_TODAY_HTML_OUTPUT)
    p_demo.add_argument("--bank-output", default=DEFAULT_BANK_OUTPUT)
    p_demo.add_argument("--open", action=argparse.BooleanOptionalAction, default=True, help="生成后是否自动打开浏览器")
    p_demo.add_argument("--vault", default=get_obsidian_vault_path(), help="Obsidian vault 路径")
    p_demo.add_argument("--use-llm", action="store_true", help="使用 .env 中配置的 LLM API 生成答案")
    add_db_argument(p_demo)
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main() -> None:
    """Parse CLI arguments and dispatch to the selected command."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()

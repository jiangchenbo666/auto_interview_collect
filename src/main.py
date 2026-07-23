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
from src.knowledge.obsidian import retrieve_relevant_snippets
from src.processors.extractor import extract_questions
from src.scheduler.daily_job import rebuild_answers, process_pending_questions, run_daily_loop, run_daily_push
from src.storage.db import init_db
from src.storage import repository
from src.viewer.html_builder import build_today_html


DEFAULT_TODAY_OUTPUT = "data/exports/today.md"
DEFAULT_TODAY_HTML_OUTPUT = "data/exports/today.html"
DEFAULT_BANK_OUTPUT = "data/exports/questions.md"


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


def cmd_daily(args: argparse.Namespace) -> None:
    """Build today's review markdown; send it unless dry-run is enabled."""
    init_db(args.db)
    markdown = run_daily_push(args.db, limit=args.limit, dry_run=args.dry_run)
    if args.output:
        write_text_file(args.output, markdown)
        print(f"Saved daily review to {args.output}\n")
    print(markdown)
    if args.dry_run:
        print("\nDry run only. Nothing was sent.")


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
    daily_markdown = run_daily_push(args.db, limit=args.limit, dry_run=True)
    today_questions = repository.get_pending_for_daily(args.db, args.limit)
    rows = repository.export_questions(args.db)

    write_text_file(args.today_output, daily_markdown)
    write_text_file(args.html_output, build_today_html(today_questions))
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


def open_in_browser(path: str | Path) -> None:
    """Open a local file in the default browser."""
    webbrowser.open(Path(path).resolve().as_uri())


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

    p_daily = init_parser.add_parser("daily", help="生成或推送今日学习内容")
    p_daily.add_argument("--limit", type=int, default=3)
    p_daily.add_argument("--dry-run", action="store_true")
    p_daily.add_argument("--output", help="把今日复习内容保存为 Markdown 文件")
    add_db_argument(p_daily)
    p_daily.set_defaults(func=cmd_daily)

    p_serve = init_parser.add_parser("serve-daily", help="常驻进程，每天定时处理并推送")
    p_serve.add_argument("--time", default="08:30", help="每日推送时间，格式 HH:MM")
    p_serve.add_argument("--limit", type=int, default=3)
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

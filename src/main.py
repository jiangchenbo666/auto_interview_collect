from __future__ import annotations

import argparse
import sys
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

from src.config_loader import get_db_path
from src.processors.extractor import extract_questions
from src.scheduler.daily_job import process_pending_questions, run_daily_loop, run_daily_push
from src.storage.db import init_db
from src.storage import repository


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize local database."""
    init_db(args.db)
    print(f"Initialized database: {args.db}")


def cmd_import_file(args: argparse.Namespace) -> None:
    """Read a local md/txt file, extract questions, and store them."""
    init_db(args.db)
    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    questions = extract_questions(text)
    result = repository.bulk_insert_questions(
        args.db,
        questions,
        source_url=str(path),
        source_type="file",
    )
    print(f"Extracted {len(questions)} questions.")
    print(f"Accepted {result['accepted']}, skipped {result['skipped']}.")


def cmd_process(args: argparse.Namespace) -> None:
    """Run classification and answer generation for pending questions."""
    init_db(args.db)
    count = process_pending_questions(args.db, limit=args.limit)
    print(f"Processed {count} question state transitions.")


def cmd_daily(args: argparse.Namespace) -> None:
    """Build today's review markdown; send it unless dry-run is enabled."""
    init_db(args.db)
    markdown = run_daily_push(args.db, limit=args.limit, dry_run=args.dry_run)
    print(markdown)
    if args.dry_run:
        print("\nDry run only. Nothing was sent.")


def cmd_serve_daily(args: argparse.Namespace) -> None:
    """Run a simple foreground daily scheduler."""
    init_db(args.db)
    print(f"Daily scheduler started. time={args.time}, limit={args.limit}, dry_run={args.dry_run}")
    run_daily_loop(args.db, push_time=args.time, limit=args.limit, dry_run=args.dry_run)


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
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(rows)} questions to {output}")


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
    add_db_argument(p_import)
    p_import.set_defaults(func=cmd_import_file)

    p_process = init_parser.add_parser("process", help="分类并生成答案")
    p_process.add_argument("--limit", type=int, default=20)
    add_db_argument(p_process)
    p_process.set_defaults(func=cmd_process)

    p_daily = init_parser.add_parser("daily", help="生成或推送今日学习内容")
    p_daily.add_argument("--limit", type=int, default=3)
    p_daily.add_argument("--dry-run", action="store_true")
    add_db_argument(p_daily)
    p_daily.set_defaults(func=cmd_daily)

    p_serve = init_parser.add_parser("serve-daily", help="常驻进程，每天定时处理并推送")
    p_serve.add_argument("--time", default="08:30", help="每日推送时间，格式 HH:MM")
    p_serve.add_argument("--limit", type=int, default=3)
    p_serve.add_argument("--dry-run", action="store_true")
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

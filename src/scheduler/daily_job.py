from __future__ import annotations

from pathlib import Path
import time
from datetime import datetime

"""High-level daily workflow.

这个文件是 MVP 的主业务链路：
1. 读取 raw 题目
2. 分类
3. 生成标准答案和面试表达
4. 选择今日复习题
5. dry-run 输出或真实推送
"""

from src.processors.answer_generator import generate_standard_answer
from src.processors.classifier import classify_question
from src.processors.project_adapter import build_project_answer, load_project_profile
from src.knowledge.obsidian import format_snippets, retrieve_relevant_snippets
from src.llm.provider import generate_interview_answer_with_llm, has_llm_config
from src.push.markdown_builder import build_daily_markdown
from src.push.wecom_bot import send_markdown
from src.storage import repository


def process_pending_questions(
    db_path: str | Path,
    profile_path: str | Path = "docs/project_profile.md",
    vault_path: str | Path = "data/obsidian",
    limit: int = 20,
    use_llm: bool = False,
) -> int:
    """Move pending questions through classify -> answer -> package steps."""
    profile = load_project_profile(profile_path)
    raw_questions = repository.get_questions_by_status(db_path, "raw", limit)
    classified_count = 0

    for item in raw_questions:
        category, difficulty = classify_question(item["question"])
        repository.update_question_category(db_path, item["id"], category, difficulty)
        classified_count += 1

    classified = repository.get_questions_by_status(db_path, "classified", limit)
    answered_count = 0
    for item in classified:
        category = item.get("category") or "测试基础"
        snippets = retrieve_relevant_snippets(item["question"], vault_path=vault_path)
        knowledge_context = format_snippets(snippets)
        if use_llm and has_llm_config():
            answer, project_answer = generate_interview_answer_with_llm(
                item["question"],
                category,
                knowledge_context,
                profile,
            )
        else:
            answer = generate_standard_answer(item["question"], category)
            project_answer = build_project_answer(
                item["question"],
                category,
                answer,
                f"{profile}\n\nObsidian 相关笔记：\n{knowledge_context}",
            )
        repository.update_question_answer(db_path, item["id"], answer, project_answer)
        answered_count += 1

    return classified_count + answered_count


def rebuild_answers(
    db_path: str | Path,
    profile_path: str | Path = "docs/project_profile.md",
    vault_path: str | Path = "data/obsidian",
    limit: int = 50,
    use_llm: bool = False,
) -> int:
    """Regenerate answers for existing questions after notes/profile changed."""
    profile = load_project_profile(profile_path)
    questions = repository.export_questions(db_path)[:limit]
    changed = 0

    for item in questions:
        category = item.get("category")
        if not category:
            category, difficulty = classify_question(item["question"])
            repository.update_question_category(db_path, item["id"], category, difficulty)

        snippets = retrieve_relevant_snippets(item["question"], vault_path=vault_path)
        knowledge_context = format_snippets(snippets)
        if use_llm and has_llm_config():
            answer, project_answer = generate_interview_answer_with_llm(
                item["question"],
                category,
                knowledge_context,
                profile,
            )
        else:
            answer = generate_standard_answer(item["question"], category)
            project_answer = build_project_answer(
                item["question"],
                category,
                answer,
                f"{profile}\n\nObsidian 相关笔记：\n{knowledge_context}",
            )
        repository.update_question_answer(db_path, item["id"], answer, project_answer)
        changed += 1

    return changed


def run_daily_push(
    db_path: str | Path,
    limit: int = 3,
    dry_run: bool = False,
    mark_reviewed: bool = False,
) -> str:
    """Build today's markdown and optionally send it to WeCom."""
    questions = repository.get_pending_for_daily(db_path, limit)
    markdown = build_daily_markdown(questions)
    if questions and (not dry_run or mark_reviewed):
        for item in questions:
            repository.mark_pushed(db_path, item["id"])
    if not dry_run and questions:
        send_markdown(markdown)
    return markdown


def is_sunday(now: datetime | None = None) -> bool:
    """Return True when today is Sunday."""
    return (now or datetime.now()).weekday() == 6


def get_review_questions_for_today(db_path: str | Path, limit: int = 3) -> tuple[str, list[dict]]:
    """Use weekly review on Sunday, otherwise normal daily questions."""
    if is_sunday():
        return "weekly", repository.get_weekly_review_questions(db_path, limit=max(limit, 7))
    return "daily", repository.get_pending_for_daily(db_path, limit)


def run_daily_loop(
    db_path: str | Path,
    push_time: str = "08:30",
    limit: int = 3,
    dry_run: bool = False,
    use_llm: bool = False,
    vault_path: str | Path = "data/obsidian",
) -> None:
    """A tiny foreground scheduler for local MVP usage.

    It checks time every 30 seconds. For long-term production use, prefer
    Windows Task Scheduler, cron, or a proper service manager.
    """
    last_run_date: str | None = None
    while True:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        if current_time == push_time and last_run_date != today:
            process_pending_questions(
                db_path,
                limit=50,
                use_llm=use_llm,
                vault_path=vault_path,
            )
            markdown = run_daily_push(db_path, limit=limit, dry_run=dry_run)
            print(markdown)
            last_run_date = today
        time.sleep(30)

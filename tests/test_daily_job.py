from __future__ import annotations

from src.scheduler.daily_job import process_pending_questions, run_daily_push
from src.storage.db import init_db
from src.storage import repository


def test_process_and_daily_dry_run(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    repository.insert_question(db_path, "接口测试用例应该如何设计？")
    repository.insert_question(db_path, "什么是 SQL 注入？")

    changed = process_pending_questions(db_path, limit=10)
    assert changed == 4

    markdown = run_daily_push(db_path, limit=2, dry_run=True)

    assert "今日测开面试复习" in markdown
    assert "接口测试用例应该如何设计" in markdown
    assert "什么是 SQL 注入" in markdown

from __future__ import annotations

from datetime import datetime

from src.scheduler.daily_job import get_review_questions_for_today, is_sunday
from src.storage.db import init_db
from src.storage import repository


def test_mark_reviewed_removes_question_from_daily_pending(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    first = repository.insert_question(db_path, "接口测试用例应该如何设计？")
    second = repository.insert_question(db_path, "什么是 SQL 注入？")
    repository.update_question_category(db_path, first, "接口测试")
    repository.update_question_category(db_path, second, "安全测试")

    first_batch = repository.get_pending_for_daily(db_path, limit=1)
    repository.mark_questions_pushed(db_path, [first_batch[0]["id"]])
    second_batch = repository.get_pending_for_daily(db_path, limit=1)

    assert second_batch[0]["id"] != first_batch[0]["id"]


def test_daily_prefers_real_sources_over_sample(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    sample_id = repository.insert_question(
        db_path,
        "样例题应该靠后展示？",
        source_url="data/raw/sample_questions.md",
        source_type="file",
    )
    real_id = repository.insert_question(
        db_path,
        "真实面经题应该优先展示？",
        source_url="https://example.com/real",
        source_type="public_url",
    )
    repository.update_question_category(db_path, sample_id, "测试基础")
    repository.update_question_category(db_path, real_id, "测试基础")

    rows = repository.get_pending_for_daily(db_path, limit=1)

    assert rows[0]["id"] == real_id


def test_daily_prefers_foundation_topics_over_older_real_sources(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    old_real_id = repository.insert_question(
        db_path,
        "冒烟测试和回归测试有什么区别？",
        source_url="https://example.com/real",
        source_type="public_url",
    )
    foundation_id = repository.insert_question(
        db_path,
        "MySQL 索引为什么常用 B+ 树？",
        source_url="data/raw/real_interviews/foundation_bagu.md",
        source_type="real_interview",
    )
    repository.update_question_category(db_path, old_real_id, "测试基础")
    repository.update_question_category(db_path, foundation_id, "数据库")

    rows = repository.get_pending_for_daily(db_path, limit=1)

    assert rows[0]["id"] == foundation_id


def test_count_unreviewed_ready_questions_excludes_reviewed(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    first = repository.insert_question(db_path, "MySQL 索引为什么常用 B+ 树？")
    second = repository.insert_question(db_path, "TCP 三次握手为什么不是两次？")
    repository.update_question_category(db_path, first, "数据库")
    repository.update_question_category(db_path, second, "计算机网络")
    repository.mark_questions_pushed(db_path, [first])

    assert repository.count_unreviewed_ready_questions(db_path) == 1


def test_daily_prefers_ai_foundation_topics_over_older_real_sources(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    old_real_id = repository.insert_question(
        db_path,
        "回归测试的范围怎么确定？",
        source_url="https://example.com/real",
        source_type="public_url",
    )
    ai_id = repository.insert_question(
        db_path,
        "什么是 LLM evaluation harness？",
        source_url="data/raw/real_interviews/ai_product_foundation.md",
        source_type="real_interview",
    )
    repository.update_question_category(db_path, old_real_id, "测试基础")
    repository.update_question_category(db_path, ai_id, "AI 工程")

    rows = repository.get_pending_for_daily(db_path, limit=1)

    assert rows[0]["id"] == ai_id


def test_is_sunday():
    assert is_sunday(datetime(2026, 7, 26)) is True
    assert is_sunday(datetime(2026, 7, 24)) is False


def test_weekly_review_falls_back_to_ready_questions(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    question_id = repository.insert_question(db_path, "数据库索引为什么能提升查询速度？")
    repository.update_question_category(db_path, question_id, "数据库")

    mode, rows = get_review_questions_for_today(db_path, limit=1)

    assert mode in {"daily", "weekly"}
    assert rows

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


def test_daily_mixes_foundation_ai_nowcoder_and_public_sources(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    old_ids = [
        repository.insert_question(
            db_path,
            f"普通测试基础题 {index} 应该被混合策略打散吗？",
            source_url=f"https://example.com/test-basic-{index}",
            source_type="public_url",
        )
        for index in range(1, 7)
    ]
    foundation_id = repository.insert_question(
        db_path,
        "MySQL 索引为什么常用 B+ 树？",
        source_url="data/raw/real_interviews/foundation_bagu.md",
        source_type="real_interview",
    )
    ai_id = repository.insert_question(
        db_path,
        "什么是 LLM evaluation harness？",
        source_url="data/raw/real_interviews/ai_product_foundation.md",
        source_type="real_interview",
    )
    nowcoder_id = repository.insert_question(
        db_path,
        "接口自动化怎么实现的？",
        source_url="data/raw/real_interviews/nowcoder/nowcoder-api.md",
        source_type="real_interview",
    )
    for question_id in [*old_ids, foundation_id, ai_id, nowcoder_id]:
        repository.update_question_category(db_path, question_id, "测试基础")

    rows = repository.get_pending_for_daily(db_path, limit=6)
    selected_ids = {row["id"] for row in rows}

    assert foundation_id in selected_ids
    assert ai_id in selected_ids
    assert nowcoder_id in selected_ids


def test_daily_only_returns_complete_answer_pairs_and_reuses_pushed_buckets(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    incomplete_id = repository.insert_question(
        db_path,
        "不应该发布半成品吗？",
        source_url="牛客网 | data/raw/real_interviews/nowcoder/牛客网.md",
        source_type="curated_interview",
    )
    repository.update_question_category(db_path, incomplete_id, "测试基础")
    for question, source_url, source_type, category in [
        ("MySQL 索引为什么常用 B+ 树？", "data/raw/real_interviews/foundation_bagu.md", "foundation_bagu", "数据库"),
        ("什么是 LLM evaluation harness？", "data/raw/real_interviews/ai_product_foundation.md", "ai_engineering", "AI 工程"),
        ("牛客网里的接口自动化如何实现？", "牛客网1 | data/raw/real_interviews/nowcoder/牛客网1.md", "curated_interview", "接口测试"),
    ]:
        question_id = repository.insert_question(db_path, question, source_url=source_url, source_type=source_type)
        repository.update_question_category(db_path, question_id, category)
        repository.update_question_answer(db_path, question_id, "标准答案", "面试表达")
        repository.mark_pushed(db_path, question_id)

    rows = repository.get_pending_for_daily(db_path, limit=3, require_complete_answers=True)

    assert incomplete_id not in {row["id"] for row in rows}
    assert {row["source_type"] for row in rows} == {"foundation_bagu", "ai_engineering", "curated_interview"}


def test_generation_candidates_follow_daily_mix_instead_of_old_id_order(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    old_public = repository.insert_question(
        db_path,
        "旧的公开接口题",
        source_url="https://example.com/old",
        source_type="public_url",
    )
    for question, source_url, source_type in [
        ("MySQL 索引题", "data/raw/real_interviews/foundation_bagu.md", "foundation_bagu"),
        ("LLM Harness 题", "data/raw/real_interviews/ai_product_foundation.md", "ai_engineering"),
        ("牛客网面经题", "牛客网1 | data/raw/real_interviews/nowcoder/牛客网1.md", "curated_interview"),
    ]:
        repository.insert_question(db_path, question, source_url=source_url, source_type=source_type)

    rows = repository.get_generation_candidates(db_path, "raw", limit=4)

    assert old_public in {row["id"] for row in rows}
    assert {"foundation_bagu", "ai_engineering", "curated_interview"}.issubset(
        {row["source_type"] for row in rows}
    )


def test_duplicate_nowcoder_source_promotes_existing_public_question(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    question = "问压力测试和测试流程？"
    public_id = repository.insert_question(
        db_path,
        question,
        source_url="https://www.xiaolincoding.com/interview/business_testing.html",
        source_type="public_url",
    )
    repository.update_question_category(db_path, public_id, "性能测试")

    result = repository.bulk_insert_questions(
        db_path,
        [question],
        source_url="牛客网-字节一面 | data/raw/real_interviews/nowcoder/牛客网-字节一面.md",
        source_type="nowcoder",
    )
    rows = repository.export_questions(db_path)

    assert result["accepted"] == 0
    assert rows[0]["source_type"] == "nowcoder"
    assert rows[0]["source_url"].startswith("牛客网-字节一面")


def test_daily_finds_nowcoder_even_after_many_public_candidates(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    for index in range(1, 90):
        question_id = repository.insert_question(
            db_path,
            f"公开接口测试题 {index}？",
            source_url=f"https://www.xiaolincoding.com/interview/{index}.html",
            source_type="public_url",
        )
        repository.update_question_category(db_path, question_id, "接口测试")
    nowcoder_id = repository.insert_question(
        db_path,
        "问压力测试和测试流程？",
        source_url="牛客网 | data/raw/real_interviews/nowcoder/牛客网.md",
        source_type="nowcoder",
    )
    repository.update_question_category(db_path, nowcoder_id, "性能测试")

    rows = repository.get_pending_for_daily(db_path, limit=6)

    assert nowcoder_id in {row["id"] for row in rows}


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

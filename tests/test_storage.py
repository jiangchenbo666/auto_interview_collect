from __future__ import annotations

from src.storage.db import init_db
from src.storage import repository


def test_insert_deduplicate_and_update(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)

    first_id = repository.insert_question(db_path, "接口测试用例应该如何设计？")
    second_id = repository.insert_question(db_path, "接口测试用例应该如何设计?")

    assert first_id == second_id

    raw = repository.get_questions_by_status(db_path, "raw")
    assert len(raw) == 1

    repository.update_question_category(db_path, first_id, "接口测试", "medium")
    classified = repository.get_questions_by_status(db_path, "classified")
    assert classified[0]["category"] == "接口测试"

    repository.update_question_answer(db_path, first_id, "标准答案", "项目答案")
    packaged = repository.get_questions_by_status(db_path, "packaged")
    assert packaged[0]["answer"] == "标准答案"

    repository.mark_pushed(db_path, first_id)
    pushed = repository.get_questions_by_status(db_path, "pushed")
    assert pushed[0]["review_count"] == 1


def test_bulk_insert_counts_duplicates(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)

    result = repository.bulk_insert_questions(
        db_path,
        ["什么是 SQL 注入？", "什么是 SQL 注入?", "   "],
    )

    assert result == {"accepted": 1, "skipped": 2}

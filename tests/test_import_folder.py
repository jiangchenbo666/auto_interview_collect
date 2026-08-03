from __future__ import annotations

from argparse import Namespace

from src.main import cmd_import_folder
from src.storage.db import init_db
from src.storage.repository import export_questions


def test_import_folder_records_real_source(tmp_path):
    folder = tmp_path / "real"
    folder.mkdir()
    source = folder / "nowcoder-test.md"
    source.write_text("1. 接口测试用例应该如何设计？", encoding="utf-8")
    db_path = tmp_path / "interview.db"
    init_db(db_path)

    cmd_import_folder(
        Namespace(
            db=str(db_path),
            path=str(folder),
            source_type="nowcoder",
        )
    )

    rows = export_questions(db_path)
    assert len(rows) == 1
    assert rows[0]["source_type"] == "nowcoder"
    assert "nowcoder-test.md" in rows[0]["source_url"]


def test_import_folder_splits_multi_question_nowcoder_file(tmp_path):
    folder = tmp_path / "real"
    folder.mkdir()
    source = folder / "牛客网-字节一面.md"
    source.write_text(
        """
        # 牛客网-字节一面

        问压力测试和测试流程
        - 正确答案：压力测试是性能测试的一种。

        问接口自动化怎么实现的
        - 正确答案：可以用 requests + pytest。
        """,
        encoding="utf-8",
    )
    db_path = tmp_path / "interview.db"
    init_db(db_path)

    cmd_import_folder(
        Namespace(
            db=str(db_path),
            path=str(folder),
            source_type="real_interview",
        )
    )

    rows = export_questions(db_path)
    questions = {row["question"] for row in rows}

    assert len(rows) == 2
    assert "压力测试和测试流程" in questions
    assert "接口自动化怎么实现的" in questions
    assert all(row["source_type"] == "curated_interview" for row in rows)
    assert all(row["source_url"].startswith("牛客网-字节一面") for row in rows)

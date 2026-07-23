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

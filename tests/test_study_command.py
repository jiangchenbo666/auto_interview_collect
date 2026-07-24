from __future__ import annotations

from argparse import Namespace

from src.main import cmd_study
from src.storage.db import init_db
from src.storage import repository


def test_study_command_generates_outputs_without_refresh(tmp_path):
    db_path = tmp_path / "interview.db"
    init_db(db_path)
    question_id = repository.insert_question(db_path, "接口测试用例应该如何设计？")
    repository.update_question_category(db_path, question_id, "接口测试")

    today_output = tmp_path / "today.md"
    html_output = tmp_path / "today.html"
    bank_output = tmp_path / "questions.md"

    cmd_study(
        Namespace(
            db=str(db_path),
            refresh_sources=False,
            sources_config="config/real_sources.yaml",
            import_local=False,
            real_dir=str(tmp_path / "real_interviews"),
            vault=str(tmp_path / "obsidian"),
            use_llm=False,
            process_limit=5,
            limit=1,
            today_output=str(today_output),
            html_output=str(html_output),
            bank_output=str(bank_output),
            mark_reviewed=True,
            open=False,
        )
    )

    assert today_output.exists()
    assert html_output.exists()
    pushed = repository.get_questions_by_status(db_path, "pushed", limit=5)
    assert len(pushed) == 1

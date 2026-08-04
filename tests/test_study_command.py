from __future__ import annotations

from argparse import Namespace

from src.main import append_inventory_notice, cmd_study, prepend_page_link
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
            normalize_inbox=False,
            inbox_dir=str(tmp_path / "inbox"),
            obsidian_inbox_dir=str(tmp_path / "obsidian_inbox"),
            normalized_inbox_dir=str(tmp_path / "normalized"),
            overwrite_inbox=False,
            vault=str(tmp_path / "obsidian"),
            use_llm=False,
            process_limit=5,
            limit=1,
            low_inventory_threshold=30,
            today_output=str(today_output),
            html_output=str(html_output),
            bank_output=str(bank_output),
            mark_reviewed=True,
            open=False,
        )
    )

    assert today_output.exists()
    assert html_output.exists()
    assert "待生成" not in today_output.read_text(encoding="utf-8")
    pushed = repository.get_questions_by_status(db_path, "pushed", limit=5)
    assert len(pushed) == 1


def test_prepend_page_link_adds_pages_entry():
    markdown = prepend_page_link("# 今日复习", "https://example.github.io/project/")

    assert markdown.startswith("完整复习页：[https://example.github.io/project/]")
    assert "# 今日复习" in markdown


def test_append_inventory_notice_warns_when_low():
    markdown = append_inventory_notice(
        "# 今日复习",
        shown_count=6,
        requested_count=8,
        remaining_after_today=5,
        low_inventory_threshold=30,
    )

    assert "资料库提醒" in markdown
    assert "6/8" in markdown
    assert "未复习可推送题约 5 道" in markdown

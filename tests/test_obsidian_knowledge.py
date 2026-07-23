from __future__ import annotations

from src.knowledge.obsidian import format_snippets, retrieve_relevant_snippets


def test_retrieve_relevant_obsidian_snippets(tmp_path):
    vault = tmp_path / "obsidian"
    vault.mkdir()
    note = vault / "接口测试项目.md"
    note.write_text(
        "# 接口测试项目\n\n我在实习项目里负责接口自动化测试，重点验证 token 鉴权、越权访问和异常参数。",
        encoding="utf-8",
    )

    snippets = retrieve_relevant_snippets("接口测试如何设计鉴权用例？", vault_path=vault)

    assert snippets
    assert snippets[0].title == "接口测试项目"
    assert "token 鉴权" in snippets[0].text
    assert "接口测试项目" in format_snippets(snippets)

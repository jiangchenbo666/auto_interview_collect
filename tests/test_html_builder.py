from __future__ import annotations

from src.viewer.html_builder import build_today_html


def test_build_today_html_escapes_content():
    html = build_today_html(
        [
            {
                "question": "接口测试 <script> 应该如何设计？",
                "category": "接口测试",
                "difficulty": "medium",
                "answer": "标准答案",
                "project_answer": "面试表达",
            }
        ]
    )

    assert "今日测开面试复习" in html
    assert "&lt;script&gt;" in html
    assert "接口测试" in html


def test_build_today_html_supports_weekly_mode():
    html = build_today_html([], mode="weekly")

    assert "周日精选复习" in html


def test_build_today_html_renders_obsidian_evidence():
    html = build_today_html(
        [
            {
                "question": "接口鉴权怎么测？",
                "answer": "标准答案",
                "project_answer": "结合项目回答",
                "knowledge_evidence": [
                    {
                        "title": "权限测试项目",
                        "path": "data/obsidian/project.md",
                        "score": 6,
                        "text": "我在实习项目里补充过接口鉴权、越权和 token 过期用例。",
                    }
                ],
            }
        ]
    )

    assert "Obsidian Evidence" in html
    assert "权限测试项目" in html
    assert "data/obsidian/project.md" in html

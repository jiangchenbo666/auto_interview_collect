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

from __future__ import annotations

from typing import Any


def build_daily_markdown(questions: list[dict[str, Any]]) -> str:
    """Format selected questions into WeCom-compatible markdown."""
    lines = ["# 今日测开面试复习", ""]
    if not questions:
        return "# 今日测开面试复习\n\n暂无待推送题目，可以先导入新的面经。"

    for index, item in enumerate(questions, start=1):
        lines.extend(
            [
                f"## {index}. {item['question']}",
                f"题型：{infer_topic_type(item)}",
                f"分类：{item.get('category') or '未分类'}",
                f"难度：{item.get('difficulty') or 'medium'}",
                f"来源：{item.get('source_url') or '未记录'}",
                "",
                "标准答案：",
                item.get("answer") or "待生成",
                "",
                "面试表达：",
                item.get("project_answer") or item.get("answer") or "待生成",
                "",
                "---",
                "",
            ]
        )
    lines.append("今日建议：每道题用 1 分钟复述，重点记关键词和项目落地点。")
    return "\n".join(lines).strip()


def infer_topic_type(item: dict[str, Any]) -> str:
    """Derive a user-facing topic type from the source path and category."""
    source = str(item.get("source_url") or "").lower()
    category = str(item.get("category") or "")
    if "foundation_bagu" in source:
        return "八股底盘"
    if "ai_product_foundation" in source or category in {"AI 工程", "RAG 与 LLM 应用"}:
        return "AI 工程"
    if "nowcoder" in source or "牛客" in source:
        return "真实面经"
    if "sample_questions" in source:
        return "Demo 样例"
    return "面试题"

from __future__ import annotations

import re
from html import escape
from typing import Any


def build_today_html(questions: list[dict[str, Any]], mode: str = "daily") -> str:
    """Render today's review questions as a standalone HTML page."""
    page_title = "周日精选复习" if mode == "weekly" else "今日测开面试复习"
    subtitle = "本页自动切换为周日精选，适合回看本周已经学过和高频题。" if mode == "weekly" else "建议每道题用 1 分钟复述，重点记关键词和项目落地点。"
    cards = "\n".join(build_question_card(index, item) for index, item in enumerate(questions, 1))
    if not cards:
        cards = """
        <section class="empty">
          <h2>暂无待复习题目</h2>
          <p>先导入一份 md/txt 面经，然后重新运行 demo。</p>
        </section>
        """

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #667085;
      --line: #d9dee8;
      --accent: #2563eb;
      --accent-soft: #e8f0ff;
      --ok-soft: #ecfdf3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      line-height: 1.7;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 28px 32px 22px;
    }}
    main {{
      max-width: 1040px;
      margin: 0 auto;
      padding: 24px 20px 56px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      font-weight: 750;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }}
    .toolbar {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}
    .pill {{
      border: 1px solid var(--line);
      background: var(--accent-soft);
      color: #174ea6;
      border-radius: 999px;
      padding: 4px 11px;
      font-size: 13px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
      margin: 18px 0;
    }}
    .card h2 {{
      margin: 0 0 12px;
      font-size: 22px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    .meta {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}
    .tag {{
      background: var(--ok-soft);
      border: 1px solid #bbf7d0;
      border-radius: 999px;
      color: #166534;
      padding: 3px 10px;
      font-size: 13px;
    }}
    .section-title {{
      margin: 18px 0 6px;
      color: var(--accent);
      font-size: 15px;
      font-weight: 700;
    }}
    .source {{
      color: var(--muted);
      font-size: 13px;
      margin: -6px 0 14px;
      word-break: break-all;
    }}
    .answer {{
      white-space: pre-wrap;
      margin: 0;
      color: #253041;
    }}
    .evidence-list {{
      display: grid;
      gap: 10px;
      margin-top: 8px;
    }}
    .evidence {{
      border-left: 3px solid var(--accent);
      background: #f8fafc;
      padding: 10px 12px;
      font-size: 13px;
    }}
    .evidence-title {{
      margin: 0 0 4px;
      font-weight: 700;
    }}
    .evidence-path {{
      color: var(--muted);
      margin: 0 0 6px;
      word-break: break-all;
    }}
    .evidence-text {{
      margin: 0;
      white-space: pre-wrap;
      color: #344054;
    }}
    .empty {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 32px;
      margin-top: 20px;
    }}
    footer {{
      color: var(--muted);
      font-size: 14px;
      margin-top: 24px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{page_title}</h1>
    <p class="subtitle">{subtitle}</p>
    <div class="toolbar">
      <span class="pill">今日 {len(questions)} 道题</span>
      <span class="pill">本地 HTML 预览</span>
      <span class="pill">不需要微信配置</span>
    </div>
  </header>
  <main>
    {cards}
    <footer>由 auto_interview_collect 生成。修改 docs/project_profile.md 可以让回答更像你的真实经历。</footer>
  </main>
</body>
</html>
"""


def build_question_card(index: int, item: dict[str, Any]) -> str:
    """Render one review question card."""
    question = escape(str(item.get("question") or "未命名题目"))
    category = escape(str(item.get("category") or "未分类"))
    difficulty = escape(str(item.get("difficulty") or "medium"))
    source = escape(str(item.get("source_url") or "未记录"))
    answer = escape(str(item.get("answer") or "待生成"))
    project_answer = escape(str(item.get("project_answer") or item.get("answer") or "待生成"))
    evidence = build_evidence_block(item.get("knowledge_evidence") or [])

    return f"""
    <article class="card">
      <h2>{index}. {question}</h2>
      <div class="meta">
        <span class="tag">分类：{category}</span>
        <span class="tag">难度：{difficulty}</span>
      </div>
      <div class="source">来源：{source}</div>
      <div class="section-title">标准答案</div>
      <p class="answer">{answer}</p>
      <div class="section-title">面试表达</div>
      <p class="answer">{project_answer}</p>
      {evidence}
    </article>
    """


def build_evidence_block(evidence_items: list[dict[str, Any]]) -> str:
    """Render Obsidian retrieval evidence so users can audit answer grounding."""
    if not evidence_items:
        return """
      <div class="section-title">Obsidian Evidence</div>
      <p class="source">No matching Obsidian note snippets were found for this question.</p>
        """

    cards = []
    for item in evidence_items:
        title = escape(str(item.get("title") or "Untitled note"))
        path = escape(str(item.get("path") or "unknown path"))
        score = escape(str(item.get("score") or 0))
        text = escape(compact_text(str(item.get("text") or "")))
        cards.append(
            f"""
        <div class="evidence">
          <p class="evidence-title">{title} · score {score}</p>
          <p class="evidence-path">{path}</p>
          <p class="evidence-text">{text}</p>
        </div>
            """
        )

    return f"""
      <div class="section-title">Obsidian Evidence</div>
      <div class="evidence-list">
        {"".join(cards)}
      </div>
    """


def compact_text(text: str, max_chars: int = 260) -> str:
    """Keep evidence snippets short enough for a study card."""
    compacted = re.sub(r"\s+", " ", text).strip()
    if len(compacted) <= max_chars:
        return compacted
    return compacted[:max_chars].rstrip() + "..."

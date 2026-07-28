from __future__ import annotations

import os

from src.llm.openai_client import build_prompt, split_answer_sections
from src.push.wecom_bot import load_env_file


DEFAULT_KIMI_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_KIMI_MODEL = "kimi-k2.6"


def generate_interview_answer_with_kimi(
    question: str,
    category: str,
    knowledge_context: str,
    project_profile: str,
    model: str | None = None,
) -> tuple[str, str]:
    """Generate answers with Kimi/Moonshot's OpenAI-compatible API."""
    load_env_file()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("请先安装依赖：pip install -r requirements.txt") from exc

    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 KIMI_API_KEY 或 MOONSHOT_API_KEY，请写入 .env 或 GitHub Secrets。")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("KIMI_BASE_URL")
        or os.getenv("MOONSHOT_BASE_URL")
        or DEFAULT_KIMI_BASE_URL,
    )
    response = client.chat.completions.create(
        model=model or os.getenv("KIMI_MODEL") or os.getenv("MOONSHOT_MODEL") or DEFAULT_KIMI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是测试开发/安全测试方向的面试辅导助手，回答要准确、具体、像候选人能口述的话。",
            },
            {
                "role": "user",
                "content": build_prompt(question, category, knowledge_context, project_profile),
            },
        ],
        stream=False,
    )
    text = response.choices[0].message.content or ""
    return split_answer_sections(text)

from __future__ import annotations

import os

from src.llm.openai_client import build_prompt, llm_max_tokens, llm_timeout_seconds, split_answer_sections
from src.push.wecom_bot import load_env_file


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"


def generate_interview_answer_with_deepseek(
    question: str,
    category: str,
    knowledge_context: str,
    project_profile: str,
    model: str | None = None,
) -> tuple[str, str]:
    """Generate answers with DeepSeek's OpenAI-compatible API."""
    load_env_file()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("请先安装依赖：pip install -r requirements.txt") from exc

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY，请写入 .env。")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
        timeout=llm_timeout_seconds(),
        max_retries=0,
    )
    response = client.chat.completions.create(
        model=model or os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
        max_tokens=llm_max_tokens(),
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

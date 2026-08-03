from __future__ import annotations

import os
from typing import Any

from src.push.wecom_bot import load_env_file


DEFAULT_OPENAI_MODEL = "gpt-5"
DEFAULT_LLM_TIMEOUT_SECONDS = 120.0
DEFAULT_LLM_MAX_TOKENS = 1400


def has_openai_config() -> bool:
    """Return True when OPENAI_API_KEY is available."""
    load_env_file()
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_interview_answer_with_openai(
    question: str,
    category: str,
    knowledge_context: str,
    project_profile: str,
    model: str | None = None,
) -> tuple[str, str]:
    """Generate standard and interview answers with the OpenAI Python SDK.

    The import stays inside the function so local-only users do not need the
    OpenAI package until they actually enable API-backed generation.
    """
    load_env_file()
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("请先安装依赖：pip install -r requirements.txt") from exc

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=llm_timeout_seconds())
    prompt = build_prompt(question, category, knowledge_context, project_profile)
    response = client.responses.create(
        model=selected_model,
        input=[
            {
                "role": "system",
                "content": "你是测试开发/安全测试方向的面试辅导助手，回答要准确、具体、像候选人能口述的话。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    text = extract_response_text(response)
    return split_answer_sections(text)


def llm_timeout_seconds() -> float:
    """Read a bounded LLM request timeout from environment."""
    raw_value = os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_LLM_TIMEOUT_SECONDS))
    try:
        return max(5.0, float(raw_value))
    except ValueError:
        return DEFAULT_LLM_TIMEOUT_SECONDS


def llm_max_tokens() -> int:
    """Read a response token cap so one interview answer does not run forever."""
    raw_value = os.getenv("LLM_MAX_TOKENS", str(DEFAULT_LLM_MAX_TOKENS))
    try:
        return max(500, int(raw_value))
    except ValueError:
        return DEFAULT_LLM_MAX_TOKENS


def build_prompt(
    question: str,
    category: str,
    knowledge_context: str,
    project_profile: str,
) -> str:
    """Build one prompt with retrieved Obsidian notes as private context."""
    return f"""请为下面这道测试开发/安全测试面试题生成答案。

题目：
{question}

分类：
{category}

我的项目/经历画像：
{project_profile}

从 Obsidian 知识库检索到的相关笔记：
{knowledge_context}

输出要求：
1. 先输出“标准答案”，讲清楚知识点、方法、注意事项。
2. 再输出“面试表达”，必须尽量结合上面的项目/经历/笔记内容。
3. 不要编造笔记里没有的公司名、指标、系统名；没有证据时用“我会/我通常”表达。
4. 语言自然，适合面试口述。

请严格使用下面格式：

标准答案：
...

面试表达：
...
"""


def extract_response_text(response: Any) -> str:
    """Extract text from the Responses API result across SDK versions."""
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(str(text))
    return "\n".join(chunks).strip()


def split_answer_sections(text: str) -> tuple[str, str]:
    """Split model output into standard answer and interview answer."""
    if "面试表达：" in text:
        before, after = text.split("面试表达：", 1)
        standard = before.replace("标准答案：", "").strip()
        interview = after.strip()
        return standard or text.strip(), interview or text.strip()
    return text.strip(), text.strip()

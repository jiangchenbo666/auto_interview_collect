from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path

from src.llm.openai_client import build_prompt, llm_timeout_seconds, split_answer_sections
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
        timeout=llm_timeout_seconds(),
        max_retries=1,
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


def extract_interview_material_from_image_with_kimi(
    image_path: str | Path,
    model: str | None = None,
) -> str:
    """Read an interview screenshot and convert it into concise markdown.

    This is intentionally stricter than generic OCR: the output should become
    a source note for later question extraction, not a long copy of someone
    else's full article/answer.
    """
    load_env_file()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("请先安装依赖：pip install -r requirements.txt") from exc

    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 KIMI_API_KEY 或 MOONSHOT_API_KEY，无法解析截图。")

    path = Path(image_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    image_data = base64.b64encode(path.read_bytes()).decode("ascii")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("KIMI_BASE_URL")
        or os.getenv("MOONSHOT_BASE_URL")
        or DEFAULT_KIMI_BASE_URL,
        timeout=llm_timeout_seconds(),
        max_retries=1,
    )
    response = client.chat.completions.create(
        model=(
            model
            or os.getenv("KIMI_VISION_MODEL")
            or os.getenv("MOONSHOT_VISION_MODEL")
            or os.getenv("KIMI_MODEL")
            or os.getenv("MOONSHOT_MODEL")
            or DEFAULT_KIMI_MODEL
        ),
        messages=[
            {
                "role": "system",
                "content": (
                    "你是面经资料整理助手。请只整理与测试开发、安全测试、AI 工程、"
                    "数据库、Linux、网络、Docker 相关的面试题。不要大段照抄截图里的答案，"
                    "有答案时压缩成要点。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "请读取这张截图，输出规范 Markdown：\n"
                            "# 标题\n"
                            "- 来源：如果截图可见就写，否则写“截图”\n"
                            "- 资料类型：牛客面经/八股/项目追问/AI工程/其他\n\n"
                            "## 抽取题目\n"
                            "1. 题目\n"
                            "2. 题目\n\n"
                            "## 可用答案要点\n"
                            "- 如果截图里有答案，只保留简短要点；如果没有答案，写“无”。\n\n"
                            "## 分类建议\n"
                            "- 给每道题一个简短分类。"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                        },
                    },
                ],
            },
        ],
        stream=False,
    )
    return response.choices[0].message.content or ""

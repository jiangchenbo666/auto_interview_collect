from __future__ import annotations

import os
from pathlib import Path

from src.llm.deepseek_client import generate_interview_answer_with_deepseek
from src.llm.kimi_client import (
    extract_interview_material_from_image_with_kimi,
    generate_interview_answer_with_kimi,
)
from src.llm.openai_client import generate_interview_answer_with_openai
from src.push.wecom_bot import load_env_file


def has_llm_config(provider: str | None = None) -> bool:
    """Check whether the selected provider has an API key configured."""
    load_env_file()
    selected = (provider or os.getenv("LLM_PROVIDER", "deepseek")).lower()
    if selected == "deepseek":
        return bool(os.getenv("DEEPSEEK_API_KEY"))
    if selected in {"kimi", "moonshot"}:
        return bool(os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY"))
    if selected == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    return False


def generate_interview_answer_with_llm(
    question: str,
    category: str,
    knowledge_context: str,
    project_profile: str,
    provider: str | None = None,
) -> tuple[str, str]:
    """Generate answers with the configured LLM provider."""
    load_env_file()
    selected = (provider or os.getenv("LLM_PROVIDER", "deepseek")).lower()
    if selected == "deepseek":
        return generate_interview_answer_with_deepseek(
            question,
            category,
            knowledge_context,
            project_profile,
        )
    if selected in {"kimi", "moonshot"}:
        return generate_interview_answer_with_kimi(
            question,
            category,
            knowledge_context,
            project_profile,
        )
    if selected == "openai":
        return generate_interview_answer_with_openai(
            question,
            category,
            knowledge_context,
            project_profile,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER: {selected}")


def extract_interview_material_from_image(
    image_path: str | Path,
    provider: str | None = None,
) -> str:
    """Use the configured multimodal provider to OCR and structure screenshots."""
    load_env_file()
    selected = (provider or os.getenv("LLM_PROVIDER", "kimi")).lower()
    if selected in {"kimi", "moonshot"}:
        return extract_interview_material_from_image_with_kimi(image_path)
    raise ValueError(f"Provider does not support image extraction yet: {selected}")

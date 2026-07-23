from __future__ import annotations

from pathlib import Path


DEFAULT_PROFILE = (
    "候选人方向是测试开发/安全测试，熟悉 Python、接口测试、Linux、数据库和基础安全测试。"
    "表达风格偏工程实践：先讲方法，再讲项目落地，最后讲结果和复盘。"
)


def load_project_profile(path: str | Path = "docs/project_profile.md") -> str:
    """Load the user's project profile used to personalize answers."""
    profile_path = Path(path)
    if not profile_path.exists():
        return DEFAULT_PROFILE
    text = profile_path.read_text(encoding="utf-8").strip()
    return text or DEFAULT_PROFILE


def build_project_answer(question: str, category: str, standard_answer: str, profile: str) -> str:
    """Wrap a standard answer into a more interview-like spoken answer."""
    opening = "如果面试官问到这个问题，我会结合自己的测试开发/安全测试实践这样回答："
    practice = (
        f"我会先把问题归到“{category}”这个方向，先说明核心思路，再落到具体测试动作。"
        "在实习或项目里，我会把它拆成可执行的检查点，比如输入、权限、异常链路、数据一致性、日志和结果验证。"
    )
    result = (
        "这样回答的好处是既能体现我理解基础知识，也能说明我真的知道怎么在项目里发现问题、定位问题并推动修复。"
    )
    profile_hint = summarize_profile(profile)
    return f"{opening}\n\n{practice}\n\n{standard_answer}\n\n结合我的背景：{profile_hint}\n\n{result}"


def summarize_profile(profile: str) -> str:
    """Keep only the first few useful profile lines for compact answers."""
    lines = [line.strip("-# ") for line in profile.splitlines() if line.strip()]
    useful = [line for line in lines if not line.startswith("请把") and len(line) > 4]
    return "；".join(useful[:3]) if useful else DEFAULT_PROFILE

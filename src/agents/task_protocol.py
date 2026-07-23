from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkerTask:
    """Structured task card for a future DeepSeek Worker Agent."""

    task_id: str
    goal: str
    context: str
    files_allowed_to_modify: list[str]
    requirements: list[str]
    constraints: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render this task as a markdown prompt/task card."""
        return "\n".join(
            [
                "# Worker Task",
                "",
                "## Task ID",
                self.task_id,
                "",
                "## Goal",
                self.goal,
                "",
                "## Context",
                self.context,
                "",
                "## Files Allowed To Modify",
                *[f"- {item}" for item in self.files_allowed_to_modify],
                "",
                "## Requirements",
                *[f"{index}. {item}" for index, item in enumerate(self.requirements, 1)],
                "",
                "## Constraints",
                *[f"- {item}" for item in self.constraints],
            ]
        )

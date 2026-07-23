from __future__ import annotations

import sqlite3
from pathlib import Path


# 题库主表。MVP 先用单表承载问题、答案、分类和推送状态，
# 后续如果要做标签、多轮复习、全文搜索，再拆表也来得及。
SCHEMA = """
CREATE TABLE IF NOT EXISTS interview_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    question_hash TEXT NOT NULL UNIQUE,
    category TEXT,
    answer TEXT,
    project_answer TEXT,
    source_url TEXT,
    source_type TEXT,
    difficulty TEXT DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'raw',
    review_count INTEGER NOT NULL DEFAULT 0,
    last_pushed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_interview_questions_status
ON interview_questions(status);

CREATE INDEX IF NOT EXISTS idx_interview_questions_category
ON interview_questions(category);
"""


def ensure_parent(db_path: str | Path) -> None:
    """Ensure the database folder exists before sqlite connects."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection and return rows as dict-like sqlite3.Row."""
    ensure_parent(db_path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str | Path) -> None:
    """Create database tables and indexes if they do not exist."""
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)

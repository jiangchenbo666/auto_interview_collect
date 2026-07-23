from __future__ import annotations

import os
from pathlib import Path

from src.push.wecom_bot import load_env_file


DEFAULT_DB_PATH = "data/interview.db"


def get_db_path() -> str:
    """Read database path from .env, falling back to data/interview.db."""
    load_env_file()
    return os.getenv("INTERVIEW_DB_PATH", DEFAULT_DB_PATH)


def project_root() -> Path:
    """Return repository root based on this file location."""
    return Path(__file__).resolve().parents[1]

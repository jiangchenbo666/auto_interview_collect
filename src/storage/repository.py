from __future__ import annotations

from pathlib import Path
from typing import Any

"""Repository layer for interview questions.

这个文件只负责数据库读写，不做题目抽取、分类、答案生成。
这样后面替换 DeepSeek 或增加爬虫时，不会影响存储层。
"""

from src.storage.db import connect
from src.utils.hash import question_hash


def row_to_dict(row: Any) -> dict[str, Any]:
    """Convert sqlite3.Row to a normal dict for easier downstream use."""
    return dict(row)


def insert_question(
    db_path: str | Path,
    question: str,
    source_url: str | None = None,
    source_type: str | None = "manual",
    category: str | None = None,
) -> int | None:
    """Insert one question and return its id.

    question_hash has a UNIQUE constraint, so repeated questions reuse the
    existing row id instead of creating duplicates.
    """
    clean_question = question.strip()
    if not clean_question:
        return None

    q_hash = question_hash(clean_question)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO interview_questions
            (question, question_hash, source_url, source_type, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                clean_question,
                q_hash,
                source_url,
                source_type,
                category,
                "classified" if category else "raw",
            ),
        )
        if cursor.rowcount == 0:
            existing = connection.execute(
                "SELECT id FROM interview_questions WHERE question_hash = ?",
                (q_hash,),
            ).fetchone()
            return int(existing["id"]) if existing else None
        return int(cursor.lastrowid)


def bulk_insert_questions(
    db_path: str | Path,
    questions: list[str],
    source_url: str | None = None,
    source_type: str | None = "manual",
) -> dict[str, int]:
    """Insert many extracted questions and count accepted/skipped rows."""
    inserted = 0
    duplicated_or_empty = 0
    seen_hashes: set[str] = set()

    for question in questions:
        clean_question = question.strip()
        if not clean_question:
            duplicated_or_empty += 1
            continue
        q_hash = question_hash(clean_question)
        if q_hash in seen_hashes or question_exists(db_path, q_hash):
            duplicated_or_empty += 1
            continue
        inserted_id = insert_question(db_path, clean_question, source_url, source_type)
        if inserted_id is None:
            duplicated_or_empty += 1
        else:
            seen_hashes.add(q_hash)
            inserted += 1

    return {"accepted": inserted, "skipped": duplicated_or_empty}


def question_exists(db_path: str | Path, q_hash: str) -> bool:
    """Check whether a normalized question hash already exists."""
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT 1 FROM interview_questions WHERE question_hash = ?",
            (q_hash,),
        ).fetchone()
    return row is not None


def get_questions_by_status(
    db_path: str | Path,
    status: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Fetch questions in a specific processing status."""
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM interview_questions
            WHERE status = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_pending_for_daily(db_path: str | Path, limit: int = 3) -> list[dict[str, Any]]:
    """Pick questions ready for daily review.

    Priority:
    1. Foundation topics added for the current study plan
    2. Real sources before bundled samples
    3. Never pushed before, then lower review_count, then older id
    """
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM interview_questions
            WHERE status IN ('packaged', 'answered', 'classified')
            ORDER BY
                CASE
                    WHEN COALESCE(source_url, '') LIKE '%foundation_bagu.md%' THEN 0
                    WHEN COALESCE(source_url, '') LIKE '%sample_questions.md%' THEN 2
                    ELSE 1
                END ASC,
                COALESCE(last_pushed_at, ''),
                review_count ASC,
                id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_weekly_review_questions(db_path: str | Path, limit: int = 10) -> list[dict[str, Any]]:
    """Pick recently reviewed questions for a Sunday weekly review."""
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM interview_questions
            WHERE status = 'pushed'
            ORDER BY last_pushed_at DESC, review_count DESC, id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        if len(rows) < limit:
            extra_rows = connection.execute(
                """
                SELECT * FROM interview_questions
                WHERE status IN ('packaged', 'answered', 'classified')
                ORDER BY
                    CASE
                        WHEN COALESCE(source_url, '') LIKE '%foundation_bagu.md%' THEN 0
                        WHEN COALESCE(source_url, '') LIKE '%sample_questions.md%' THEN 2
                        ELSE 1
                    END ASC,
                    review_count DESC,
                    id ASC
                LIMIT ?
                """,
                (limit - len(rows),),
            ).fetchall()
            rows = rows + extra_rows
    return [row_to_dict(row) for row in rows]


def mark_questions_pushed(db_path: str | Path, question_ids: list[int]) -> None:
    """Mark multiple questions as displayed/reviewed."""
    for question_id in question_ids:
        mark_pushed(db_path, question_id)


def mark_ignored(db_path: str | Path, question_id: int) -> None:
    """Mark one noisy/non-question row as ignored."""
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE interview_questions
            SET status = 'ignored',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (question_id,),
        )


def update_question_category(
    db_path: str | Path,
    question_id: int,
    category: str,
    difficulty: str = "medium",
) -> None:
    """Move a raw question into classified status."""
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE interview_questions
            SET category = ?, difficulty = ?, status = 'classified',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (category, difficulty, question_id),
        )


def update_question_answer(
    db_path: str | Path,
    question_id: int,
    answer: str,
    project_answer: str | None = None,
) -> None:
    """Save generated answers and move status to answered/packaged."""
    status = "packaged" if project_answer else "answered"
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE interview_questions
            SET answer = ?, project_answer = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (answer, project_answer, status, question_id),
        )


def mark_pushed(db_path: str | Path, question_id: int) -> None:
    """Mark one question as pushed and increase its review count."""
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE interview_questions
            SET status = 'pushed',
                review_count = review_count + 1,
                last_pushed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (question_id,),
        )


def list_questions(db_path: str | Path, limit: int = 20) -> list[dict[str, Any]]:
    """List newest questions for CLI inspection."""
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM interview_questions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def export_questions(db_path: str | Path) -> list[dict[str, Any]]:
    """Export all questions in stable id order."""
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM interview_questions ORDER BY id ASC"
        ).fetchall()
    return [row_to_dict(row) for row in rows]

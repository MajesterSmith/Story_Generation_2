from db.database import get_db
from config import TOKEN_ESTIMATION_CHARS_PER_TOKEN


def _est(text: str) -> int:
    return max(1, len(text) // TOKEN_ESTIMATION_CHARS_PER_TOKEN)


def add_log(world_id: int, turn_number: int, role: str, content: str, is_summary: bool = False):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO story_logs
               (world_id, turn_number, role, content, token_count, is_summary)
               VALUES (?,?,?,?,?,?)""",
            (world_id, turn_number, role, content, _est(content), 1 if is_summary else 0),
        )


def get_total_active_tokens(world_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT SUM(token_count) as total FROM story_logs WHERE world_id=? AND is_summary != 2",
            (world_id,),
        ).fetchone()
        return row["total"] or 0


def get_recent_logs(world_id: int, limit: int = 20) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM story_logs WHERE world_id=? AND is_summary != 2
               ORDER BY id DESC LIMIT ?""",
            (world_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def get_all_raw_logs(world_id: int) -> list[dict]:
    """All non-archived logs; used as input to the summarisation call."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM story_logs WHERE world_id=? AND is_summary != 2 ORDER BY id ASC",
            (world_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_display_logs(world_id: int) -> list[dict]:
    """All non-archived logs for rendering in the narrative panel."""
    return get_all_raw_logs(world_id)


def archive_and_replace_with_summary(world_id: int, summary_text: str):
    """Move raw logs to archive (is_summary=2) and store the new summary."""
    with get_db() as conn:
        conn.execute(
            "UPDATE story_logs SET is_summary=2 WHERE world_id=? AND is_summary != 2",
            (world_id,),
        )
        conn.execute(
            """INSERT INTO story_logs
               (world_id, turn_number, role, content, token_count, is_summary)
               VALUES (?,0,'system',?,?,1)""",
            (world_id, summary_text, _est(summary_text)),
        )


def get_next_turn_number(world_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT MAX(turn_number) as mx FROM story_logs WHERE world_id=?", (world_id,)
        ).fetchone()
        return (row["mx"] or 0) + 1

from config import SUMMARIZE_TOKEN_THRESHOLD
from db import story_repo


def should_summarize(world_id: int) -> bool:
    """Return True when active story tokens exceed the configured threshold."""
    return story_repo.get_total_active_tokens(world_id) >= SUMMARIZE_TOKEN_THRESHOLD


def build_context_string(world_id: int, limit: int = 12) -> tuple[str, str]:
    """
    Return (recent_story_str, major_beats_str).
    Recent story comes from recent logs; major beats from the story_beats table.
    """
    # 1. Recent Logs
    logs  = story_repo.get_recent_logs(world_id, limit=limit)
    lines = []
    for log in logs:
        prefix = {"player": "YOU", "narrator": "NARRATOR", "system": "SYSTEM"}.get(
            log["role"], log["role"].upper()
        )
        lines.append(f"[{prefix}] {log['content']}")
    recent_story = "\n".join(lines) if lines else "The story is just beginning…"

    # 2. Major Beats
    beats = story_repo.get_story_beats(world_id)
    beat_lines = [f"- {b['beat_summary']} (Turn {b['turn_number']})" for b in beats]
    major_beats = "\n".join(beat_lines) if beat_lines else ""

    return recent_story, major_beats

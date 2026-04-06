from config import SUMMARIZE_TOKEN_THRESHOLD
from db import story_repo


def should_summarize(world_id: int) -> bool:
    """Return True when active story tokens exceed the configured threshold."""
    return story_repo.get_total_active_tokens(world_id) >= SUMMARIZE_TOKEN_THRESHOLD


def build_context_string(world_id: int, limit: int = 12) -> str:
    """Return a plain-text story context string from recent logs."""
    logs  = story_repo.get_recent_logs(world_id, limit=limit)
    lines = []
    for log in logs:
        prefix = {"player": "YOU", "narrator": "NARRATOR", "system": "SYSTEM"}.get(
            log["role"], log["role"].upper()
        )
        lines.append(f"[{prefix}] {log['content']}")
    return "\n".join(lines) if lines else "The story is just beginning…"

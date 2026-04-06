import json
from db.database import get_db


def create_quest(world_id: int, player_id: int, title: str, description: str,
                 objective: str, hints: list, reward_gold: int, reward_items: list) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO quests
               (world_id, player_id, title, description, objective, status, hints, reward_gold, reward_items)
               VALUES (?,?,?,?,?,'ACTIVE',?,?,?)""",
            (world_id, player_id, title, description, objective,
             json.dumps(hints), reward_gold, json.dumps(reward_items)),
        )
        return cur.lastrowid


def get_active_quest(world_id: int, player_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            """SELECT * FROM quests
               WHERE world_id=? AND player_id=? AND status='ACTIVE'
               ORDER BY id DESC LIMIT 1""",
            (world_id, player_id),
        ).fetchone()
        if row:
            d = dict(row)
            d["hints"]        = json.loads(d.get("hints", "[]"))
            d["reward_items"] = json.loads(d.get("reward_items", "[]"))
            return d
        return None


def get_all_quests(world_id: int, player_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM quests WHERE world_id=? AND player_id=? ORDER BY id",
            (world_id, player_id),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["hints"]        = json.loads(d.get("hints", "[]"))
            d["reward_items"] = json.loads(d.get("reward_items", "[]"))
            result.append(d)
        return result


def update_quest_status(quest_id: int, status: str):
    with get_db() as conn:
        conn.execute("UPDATE quests SET status=? WHERE id=?", (status, quest_id))


def update_quest(quest_id: int, **kwargs):
    """Update Any field in the quests table."""
    if not kwargs:
        return
    
    cols = []
    vals = []
    for k, v in kwargs.items():
        if k in ("title", "description", "objective", "status", "hints", "reward_gold", "reward_items"):
            cols.append(f"{k} = ?")
            if k in ("hints", "reward_items"):
                vals.append(json.dumps(v))
            else:
                vals.append(v)
    
    if not cols:
        return
        
    vals.append(quest_id)
    with get_db() as conn:
        conn.execute(f"UPDATE quests SET {', '.join(cols)} WHERE id = ?", tuple(vals))

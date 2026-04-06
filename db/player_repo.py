import json
from db.database import get_db
from config import DEFAULT_STRENGTH, DEFAULT_INTELLIGENCE, DEFAULT_AGILITY, DEFAULT_HEALTH, DEFAULT_GOLD


def create_player(world_id: int, name: str, location: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO players
               (world_id, name, strength, intelligence, agility, health, max_health, gold, current_location)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (world_id, name, DEFAULT_STRENGTH, DEFAULT_INTELLIGENCE, DEFAULT_AGILITY,
             DEFAULT_HEALTH, DEFAULT_HEALTH, DEFAULT_GOLD, location),
        )
        return cur.lastrowid


def get_player(player_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        return dict(row) if row else None


def get_player_by_world(world_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM players WHERE world_id = ?", (world_id,)).fetchone()
        return dict(row) if row else None


def update_player_stats(player_id: int, **kwargs):
    if not kwargs:
        return
    # Clamp health to [1, max_health]
    if "health" in kwargs:
        player = get_player(player_id)
        if player:
            kwargs["health"] = max(1, min(kwargs["health"], player["max_health"]))
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [player_id]
    with get_db() as conn:
        conn.execute(f"UPDATE players SET {fields} WHERE id = ?", values)


def get_inventory(player_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM inventory WHERE player_id = ?", (player_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["properties"] = json.loads(d.get("properties", "{}"))
            result.append(d)
        return result


def add_item(player_id: int, item_name: str, item_type: str = "misc",
             quantity: int = 1, properties: dict | None = None):
    props = properties or {}
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, quantity FROM inventory WHERE player_id = ? AND item_name = ?",
            (player_id, item_name),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE inventory SET quantity = ? WHERE id = ?",
                (row["quantity"] + quantity, row["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO inventory (player_id, item_name, item_type, quantity, properties) VALUES (?,?,?,?,?)",
                (player_id, item_name, item_type, quantity, json.dumps(props)),
            )


def remove_item(player_id: int, item_name: str, quantity: int = 1) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, quantity FROM inventory WHERE player_id = ? AND item_name = ?",
            (player_id, item_name),
        ).fetchone()
        if not row:
            return False
        new_qty = row["quantity"] - quantity
        if new_qty <= 0:
            conn.execute("DELETE FROM inventory WHERE id = ?", (row["id"],))
        else:
            conn.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, row["id"]))
        return True

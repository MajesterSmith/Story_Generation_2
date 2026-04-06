import json
from db.database import get_db
from models.world import FactionModel, NPCModel


# ── Worlds ────────────────────────────────────────────────────────────────────

def get_all_worlds() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM worlds ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def get_world(world_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM worlds WHERE id = ?", (world_id,)).fetchone()
        return dict(row) if row else None


def create_world(name: str, theme: str, scale: str, lore_summary: str, starting_location: str, custom_prompt: str = "") -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO worlds (name, theme, scale, lore_summary, starting_location, custom_prompt) VALUES (?,?,?,?,?,?)",
            (name, theme, scale, lore_summary, starting_location, custom_prompt),
        )
        return cur.lastrowid


def delete_world(world_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM worlds WHERE id = ?", (world_id,))


# ── Factions ──────────────────────────────────────────────────────────────────

def create_faction(world_id: int, faction: FactionModel) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO factions (world_id, name, description, traits) VALUES (?,?,?,?)",
            (world_id, faction.name, faction.description, json.dumps(faction.traits)),
        )
        return cur.lastrowid


def get_factions(world_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM factions WHERE world_id = ?", (world_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["traits"] = json.loads(d["traits"])
            result.append(d)
        return result


# ── NPCs ──────────────────────────────────────────────────────────────────────

def create_npc(world_id: int, faction_id: int | None, npc: NPCModel) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO npcs
               (world_id, faction_id, name, description, traits,
                strength, intelligence, agility, health, max_health, gold, shop_items)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                world_id, faction_id, npc.name, npc.description, json.dumps(npc.traits),
                npc.strength, npc.intelligence, npc.agility, npc.health, npc.health,
                npc.gold, json.dumps(npc.shop_items),
            ),
        )
        return cur.lastrowid


def get_all_npcs(world_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM npcs WHERE world_id = ?", (world_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["traits"]      = json.loads(d.get("traits", "[]"))
            d["shop_items"]  = json.loads(d.get("shop_items", "[]"))
            result.append(d)
        return result


def get_npc_by_name(world_id: int, name: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM npcs WHERE world_id = ? AND lower(name) LIKE ?",
            (world_id, f"%{name.lower()}%"),
        ).fetchone()
        if row:
            d = dict(row)
            d["traits"]     = json.loads(d.get("traits", "[]"))
            d["shop_items"] = json.loads(d.get("shop_items", "[]"))
            return d
        return None


def update_npc_health(npc_id: int, health: int):
    with get_db() as conn:
        conn.execute("UPDATE npcs SET health = ? WHERE id = ?", (health, npc_id))


# ── Geography ─────────────────────────────────────────────────────────────────

def create_location(world_id: int, loc: dict) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO locations (world_id, name, description, type, danger_level) VALUES (?,?,?,?,?)",
            (world_id, loc["name"], loc["description"], loc.get("type", "settlement"), loc.get("danger_level", 1)),
        )
        return cur.lastrowid

def get_all_locations(world_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM locations WHERE world_id = ?", (world_id,)).fetchall()
        return [dict(r) for r in rows]

def get_location_by_name(world_id: int, name: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM locations WHERE world_id = ? AND lower(name) = ?",
            (world_id, name.lower()),
        ).fetchone()
        return dict(row) if row else None

def create_connection(world_id: int, from_id: int, to_id: int, desc: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO location_connections (world_id, from_location_id, to_location_id, description) VALUES (?,?,?,?)",
            (world_id, from_id, to_id, desc),
        )

def get_connections(world_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM location_connections WHERE world_id = ?", (world_id,)).fetchall()
        return [dict(r) for r in rows]


# ── World Rules ───────────────────────────────────────────────────────────────

def create_world_rules(world_id: int, rules: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO world_rules (world_id, magic_level, tech_level, laws) VALUES (?,?,?,?)",
            (world_id, rules.get("magic_level", "Medium"), rules.get("tech_level", "Medieval"), json.dumps(rules.get("laws", []))),
        )

def get_world_rules(world_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM world_rules WHERE world_id = ?", (world_id,)).fetchone()
        if row:
            d = dict(row)
            d["laws"] = json.loads(d.get("laws", "[]"))
            return d
        return None

from db.database import get_db


def create_node(world_id: int, node_type: str, entity_id: int, label: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO graph_nodes (world_id, node_type, entity_id, label) VALUES (?,?,?,?)",
            (world_id, node_type, entity_id, label),
        )
        return cur.lastrowid


def get_nodes(world_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM graph_nodes WHERE world_id = ?", (world_id,)).fetchall()
        return [dict(r) for r in rows]


def get_node_by_label(world_id: int, label: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM graph_nodes WHERE world_id = ? AND lower(label) LIKE ?",
            (world_id, f"%{label.lower()}%"),
        ).fetchone()
        return dict(row) if row else None


def create_edge(world_id: int, source_id: int, target_id: int,
                relationship: str, weight: float = 0.5) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO graph_edges
               (world_id, source_node_id, target_node_id, relationship, weight)
               VALUES (?,?,?,?,?)""",
            (world_id, source_id, target_id, relationship, weight),
        )
        return cur.lastrowid


def get_edges(world_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT e.*,
                      sn.label AS source_label, tn.label AS target_label,
                      sn.node_type AS source_type, tn.node_type AS target_type
               FROM graph_edges e
               JOIN graph_nodes sn ON e.source_node_id = sn.id
               JOIN graph_nodes tn ON e.target_node_id = tn.id
               WHERE e.world_id = ?""",
            (world_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_edge(world_id: int, source_label: str, target_label: str,
                relationship: str, weight: float = 0.6):
    """Update existing edge or create a new one between named nodes."""
    src = get_node_by_label(world_id, source_label)
    tgt = get_node_by_label(world_id, target_label)
    if not src or not tgt:
        return
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM graph_edges WHERE world_id=? AND source_node_id=? AND target_node_id=?",
            (world_id, src["id"], tgt["id"]),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE graph_edges SET relationship=?, weight=? WHERE id=?",
                (relationship, weight, row["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO graph_edges
                   (world_id, source_node_id, target_node_id, relationship, weight)
                   VALUES (?,?,?,?,?)""",
                (world_id, src["id"], tgt["id"], relationship, weight),
            )

import sqlite3
from contextlib import contextmanager
from config import DB_PATH


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS worlds (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL,
            theme            TEXT NOT NULL,
            scale            TEXT NOT NULL,
            lore_summary     TEXT DEFAULT '',
            starting_location TEXT DEFAULT '',
            custom_prompt    TEXT DEFAULT '',
            created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS factions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id    INTEGER NOT NULL,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            traits      TEXT DEFAULT '[]',
            relationship_score INTEGER DEFAULT 0,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS npcs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id      INTEGER NOT NULL,
            faction_id    INTEGER,
            name          TEXT NOT NULL,
            description   TEXT DEFAULT '',
            traits        TEXT DEFAULT '[]',
            strength      INTEGER DEFAULT 10,
            intelligence  INTEGER DEFAULT 10,
            agility       INTEGER DEFAULT 10,
            health        INTEGER DEFAULT 50,
            max_health    INTEGER DEFAULT 50,
            gold          INTEGER DEFAULT 10,
            shop_items    TEXT DEFAULT '[]',
            relationship_score INTEGER DEFAULT 0,
            FOREIGN KEY (world_id)   REFERENCES worlds(id)   ON DELETE CASCADE,
            FOREIGN KEY (faction_id) REFERENCES factions(id)
        );

        CREATE TABLE IF NOT EXISTS npc_memories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            npc_id          INTEGER NOT NULL,
            world_id        INTEGER NOT NULL,
            turn_number     INTEGER DEFAULT 0,
            event_summary   TEXT NOT NULL,
            impact_score    INTEGER DEFAULT 0,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (npc_id)   REFERENCES npcs(id)   ON DELETE CASCADE,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS graph_nodes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id    INTEGER NOT NULL,
            node_type   TEXT NOT NULL,
            entity_id   INTEGER NOT NULL,
            label       TEXT NOT NULL,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id        INTEGER NOT NULL,
            source_node_id  INTEGER NOT NULL,
            target_node_id  INTEGER NOT NULL,
            relationship    TEXT NOT NULL DEFAULT 'Neutral',
            weight          REAL DEFAULT 0.5,
            FOREIGN KEY (world_id)        REFERENCES worlds(id)      ON DELETE CASCADE,
            FOREIGN KEY (source_node_id)  REFERENCES graph_nodes(id),
            FOREIGN KEY (target_node_id)  REFERENCES graph_nodes(id)
        );

        CREATE TABLE IF NOT EXISTS players (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id         INTEGER NOT NULL,
            name             TEXT NOT NULL,
            strength         INTEGER DEFAULT 10,
            intelligence     INTEGER DEFAULT 10,
            agility          INTEGER DEFAULT 10,
            health           INTEGER DEFAULT 100,
            max_health       INTEGER DEFAULT 100,
            gold             INTEGER DEFAULT 50,
            current_location TEXT DEFAULT '',
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id   INTEGER NOT NULL,
            item_name   TEXT NOT NULL,
            item_type   TEXT DEFAULT 'misc',
            quantity    INTEGER DEFAULT 1,
            properties  TEXT DEFAULT '{}',
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS story_logs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id     INTEGER NOT NULL,
            turn_number  INTEGER DEFAULT 0,
            role         TEXT NOT NULL,
            content      TEXT NOT NULL,
            token_count  INTEGER DEFAULT 0,
            is_summary   INTEGER DEFAULT 0,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS quests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id     INTEGER NOT NULL,
            player_id    INTEGER NOT NULL,
            title        TEXT NOT NULL,
            description  TEXT DEFAULT '',
            objective    TEXT DEFAULT '',
            status       TEXT DEFAULT 'ACTIVE',
            hints        TEXT DEFAULT '[]',
            reward_gold  INTEGER DEFAULT 0,
            reward_items TEXT DEFAULT '[]',
            FOREIGN KEY (world_id)  REFERENCES worlds(id)   ON DELETE CASCADE,
            FOREIGN KEY (player_id) REFERENCES players(id)  ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS locations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id     INTEGER NOT NULL,
            name         TEXT NOT NULL,
            description  TEXT NOT NULL,
            type         TEXT DEFAULT 'settlement',
            danger_level INTEGER DEFAULT 1,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS location_connections (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id          INTEGER NOT NULL,
            from_location_id  INTEGER NOT NULL,
            to_location_id    INTEGER NOT NULL,
            description       TEXT DEFAULT 'A path connects these two places.',
            FOREIGN KEY (world_id)         REFERENCES worlds(id) ON DELETE CASCADE,
            FOREIGN KEY (from_location_id) REFERENCES locations(id) ON DELETE CASCADE,
            FOREIGN KEY (to_location_id)   REFERENCES locations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS world_rules (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id     INTEGER NOT NULL,
            magic_level  TEXT DEFAULT 'Medium',
            tech_level   TEXT DEFAULT 'Medieval',
            laws         TEXT DEFAULT '[]',
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS story_beats (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id        INTEGER NOT NULL,
            turn_number     INTEGER NOT NULL,
            beat_summary    TEXT NOT NULL,
            importance      INTEGER DEFAULT 1,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS world_state (
            world_id        INTEGER PRIMARY KEY,
            current_turn    INTEGER DEFAULT 0,
            weather         TEXT DEFAULT 'Clear',
            time_of_day     TEXT DEFAULT 'Morning',
            is_night        INTEGER DEFAULT 0,
            FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
        );
        """)

        # Migration: Add custom_prompt to worlds if not exists
        try:
            conn.execute("ALTER TABLE worlds ADD COLUMN custom_prompt TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # Already exists

        # Migration: Add relationship_score to npcs if not exists
        try:
            conn.execute("ALTER TABLE npcs ADD COLUMN relationship_score INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Migration: Add relationship_score to factions if not exists
        try:
            conn.execute("ALTER TABLE factions ADD COLUMN relationship_score INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Migration: Add goal to npcs if not exists
        try:
            conn.execute("ALTER TABLE npcs ADD COLUMN goal TEXT DEFAULT 'Survive and thrive.'")
        except sqlite3.OperationalError:
            pass

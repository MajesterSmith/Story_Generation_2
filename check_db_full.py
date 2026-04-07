import sqlite3

def check_db():
    conn = sqlite3.connect("chronos.db")
    conn.row_factory = sqlite3.Row
    
    print("--- WORLDS ---")
    worlds = conn.execute("SELECT * FROM worlds").fetchall()
    for w in worlds:
        print(f"ID: {w['id']} | Name: {w['name']}")

    print("\n--- LOCATIONS ---")
    locs = conn.execute("SELECT * FROM locations").fetchall()
    for l in locs:
        print(f"ID: {l['id']} | WorldID: {l['world_id']} | Name: {l['name']} | Type: {l['type']}")
        
    print("\n--- CONNECTIONS ---")
    conns = conn.execute("SELECT * FROM location_connections").fetchall()
    for c in conns:
        print(f"WorldID: {c['world_id']} | From: {c['from_location_id']} | To: {c['to_location_id']}")

    conn.close()

if __name__ == "__main__":
    check_db()

from db import world_repo
from db.database import init_db

init_db()
world_id = 1 # Assuming world 1 exists from previous runs
connections = world_repo.get_connections(world_id)
print(f"Connections for World {world_id}:")
for c in connections:
    print(f"  {c['from_name']} -> {c['to_name']} ({c['description']})")

locations = world_repo.get_all_locations(world_id)
print(f"Locations for World {world_id}:")
for l in locations:
    print(f"  {l['name']} ({l['type']})")

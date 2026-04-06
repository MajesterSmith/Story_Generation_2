from db import world_repo, player_repo, graph_repo, story_repo, quest_repo
from llm.ollama_client import OllamaClient
from models.world import WorldSeed


class WorldEngine:
    def __init__(self, client: OllamaClient):
        self.client = client

    def generate_world(self, world_name: str, theme: str, scale: str,
                       player_name: str, custom_prompt: str = "") -> tuple[int, int]:
        """
        Call LLM → validate → persist everything → return (world_id, player_id).
        """
        # 1. LLM world seed
        seed: WorldSeed = self.client.generate_world(world_name, theme, scale, custom_prompt)

        # 2. Persist world
        world_id = world_repo.create_world(
            seed.world_name, seed.theme, scale,
            seed.lore_summary, seed.starting_location,
            custom_prompt=custom_prompt,
        )

        # 3. Rules
        world_repo.create_world_rules(world_id, seed.rules.model_dump())

        # 4. Locations → track name→id
        location_map: dict[str, int] = {}
        for loc in seed.locations:
            lid = world_repo.create_location(world_id, loc.model_dump())
            location_map[loc.name] = lid

        # 5. Connections
        for conn in seed.connections:
            src_id = location_map.get(conn.from_location)
            tgt_id = location_map.get(conn.to_location)
            if src_id and tgt_id:
                world_repo.create_connection(world_id, src_id, tgt_id, conn.description)

        # 6. Factions → track name→id
        faction_map: dict[str, int] = {}
        for f in seed.factions:
            fid = world_repo.create_faction(world_id, f)
            faction_map[f.name] = fid

        # 7. NPCs → track name→id
        npc_map: dict[str, int] = {}
        for npc in seed.npcs:
            fid = faction_map.get(npc.faction_name)
            nid = world_repo.create_npc(world_id, fid, npc)
            npc_map[npc.name] = nid

        # 8. Graph nodes (for visualisation)
        node_map: dict[str, int] = {}
        for fname, fid in faction_map.items():
            node_map[fname] = graph_repo.create_node(world_id, "faction", fid, fname)
        for nname, nid in npc_map.items():
            node_map[nname] = graph_repo.create_node(world_id, "npc", nid, nname)

        # 9. Graph edges
        for rel in seed.relationships:
            src = node_map.get(rel.source_name)
            tgt = node_map.get(rel.target_name)
            if src and tgt:
                graph_repo.create_edge(world_id, src, tgt, rel.relationship, rel.weight)

        # 10. Player
        player_id = player_repo.create_player(world_id, player_name, seed.starting_location)

        # 11. Initial quest
        factions = world_repo.get_factions(world_id)
        npcs     = world_repo.get_all_npcs(world_id)
        q_data   = self.client.generate_quest(
            world_repo.get_world(world_id), factions, npcs
        )
        quest_repo.create_quest(
            world_id, player_id,
            title       = q_data.get("title",        "The Unknown Path"),
            description = q_data.get("description",  ""),
            objective   = q_data.get("objective",    "Explore the world."),
            hints       = q_data.get("hints",        []),
            reward_gold = q_data.get("reward_gold",  30),
            reward_items= q_data.get("reward_items", []),
        )

        # 9. Opening Narration
        world_obj = world_repo.get_world(world_id)
        # Use simple seed data for the intro call to avoid DB roundtrips
        factions  = world_repo.get_factions(world_id)
        npcs      = world_repo.get_all_npcs(world_id)
        quest_obj = quest_repo.get_active_quest(world_id, player_id)
        
        try:
            intro_text = self.client.generate_intro(player_name, world_obj, quest_obj)
        except Exception:
            intro_text = f"You awaken in {seed.starting_location}. {seed.lore_summary}"

        story_repo.add_log(world_id, 0, "narrator", intro_text)

        return world_id, player_id

        return world_id, player_id

    def load_world(self, world_id: int) -> tuple[dict, dict]:
        """Load existing world + player pair from DB."""
        world  = world_repo.get_world(world_id)
        player = player_repo.get_player_by_world(world_id)
        return world, player

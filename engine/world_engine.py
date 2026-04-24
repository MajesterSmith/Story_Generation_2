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
        fallback_location = seed.starting_location
        if not fallback_location and seed.locations:
            fallback_location = seed.locations[0].name
        for npc in seed.npcs:
            if not npc.current_location:
                npc.current_location = fallback_location
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
        
        # Initialize World State
        world_repo.update_world_state(world_id, 0, "Clear", "Morning", 0)

        # Create Player Node in Graph for relationship tracking
        graph_repo.get_or_create_player_node(world_id, player_name)

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

    def load_world(self, world_id: int) -> tuple[dict, dict]:
        """Load existing world + player pair from DB."""
        world  = world_repo.get_world(world_id)
        player = player_repo.get_player_by_world(world_id)
        return world, player

    def run_world_pulse(self, world_id: int, state_manager: "StateManager"):
        """
        Trigger a background world event.
        Returns the narration text.
        """
        world    = world_repo.get_world(world_id)
        factions = world_repo.get_factions(world_id)
        npcs     = world_repo.get_all_npcs(world_id)
        beats    = story_repo.get_story_beats(world_id)
        beat_str = "\n".join([f"- {b['beat_summary']}" for b in beats])

        data = self.client.send_world_event(world, factions, npcs, beat_str)
        narration = data.get("event_narration", "The world shifts in the shadows.")
        
        # Apply updates
        update_data = data.get("state_update", {})
        if update_data:
            from models.llm_response import StateUpdate
            state = StateUpdate(**update_data)
            
            # Use state_manager for player-agnostic updates (factions, npcs)
            # 1. NPC updates
            if state.npc_interacted_name:
                npc = world_repo.get_npc_by_name(world_id, state.npc_interacted_name)
                if npc and state.npc_relationship_change != 0:
                    world_repo.update_npc_relationship(npc["id"], state.npc_relationship_change)
            
            # 2. Faction updates
            if state.faction_interacted_name:
                f = next((fac for fac in factions if fac["name"].lower() == state.faction_interacted_name.lower()), None)
                if f and state.faction_relationship_change != 0:
                    world_repo.update_faction_relationship(f["id"], state.faction_relationship_change)

            # 3. Story Beat
            if state.important_beat:
                turn_num = story_repo.get_next_turn_number(world_id)
                story_repo.add_story_beat(world_id, turn_num, state.important_beat)

        # Log it
        turn_num = story_repo.get_next_turn_number(world_id)
        story_repo.add_log(world_id, turn_num, "system", f"[WORLD EVENT] {narration}")

        return narration

from db import quest_repo, world_repo
from llm.ollama_client import OllamaClient


class QuestEngine:
    def __init__(self, client: OllamaClient):
        self.client = client

    def generate_quest(self, world_id: int, player_id: int) -> int:
        """Generate a new LLM quest and persist it. Returns quest_id."""
        world    = world_repo.get_world(world_id)
        factions = world_repo.get_factions(world_id)
        npcs     = world_repo.get_all_npcs(world_id)

        q_data = self.client.generate_quest(world, factions, npcs)
        return quest_repo.create_quest(
            world_id, player_id,
            title        = q_data.get("title",       "Uncharted Path"),
            description  = q_data.get("description", ""),
            objective    = q_data.get("objective",   "Explore and survive."),
            hints        = q_data.get("hints",       []),
            reward_gold  = q_data.get("reward_gold", 30),
            reward_items = q_data.get("reward_items",[]),
        )

    def get_active(self, world_id: int, player_id: int) -> dict | None:
        return quest_repo.get_active_quest(world_id, player_id)

    def complete_quest(self, quest_id: int):
        quest_repo.update_quest_status(quest_id, "COMPLETED")

    def fail_quest(self, quest_id: int):
        quest_repo.update_quest_status(quest_id, "FAILED")

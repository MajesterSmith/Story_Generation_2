from db import player_repo, world_repo, quest_repo, story_repo
from llm.ollama_client import OllamaClient
from models.llm_response import LLMResponse
from engine.state_manager import StateManager
from utils import dice, context_tracker


class NarrativeEngine:
    """
    Orchestrates a single story turn:
      validate → (maybe summarise) → dice roll → LLM → apply state → log.
    """

    def __init__(self, client: OllamaClient, state_manager: StateManager):
        self.client  = client
        self.sm      = state_manager

    # ── Public ────────────────────────────────────────────────────────────────

    def process_turn(self, world_id: int, player_id: int,
                     action: str) -> LLMResponse:

        player = player_repo.get_player(player_id)
        world  = world_repo.get_world(world_id)
        quest  = quest_repo.get_active_quest(world_id, player_id)

        # 1. Symbolic pre-flight
        validation = self.sm.validate_action(action, player)

        # 2. Summarise if context threshold exceeded
        if context_tracker.should_summarize(world_id):
            self._run_summarisation(world_id)

        # 3. Dice roll
        stat_name, stat_val = dice.determine_relevant_stat(action, player)
        dice_result = dice.roll(stat_name, stat_val)
        dice_str    = dice_result.to_prompt_string()
        if validation["notes"]:
            dice_str += f"\n[GM NOTE: {validation['notes']}]"

        # 4. Fetch rich context (Geography & Rules)
        location = world_repo.get_location_by_name(world_id, player["current_location"])
        rules    = world_repo.get_world_rules(world_id)

        # 5. Build context string
        story_ctx = context_tracker.build_context_string(world_id, limit=10)

        # 6. LLM call
        response: LLMResponse = self.client.send_turn(
            player, world, quest, action, dice_str, story_ctx,
            location=location, rules=rules
        )

        # 6. Apply state updates
        self.sm.apply_updates(player_id, world_id, response.state_update)

        # Merge narrative quest updates into the main narrative for display
        for qu in response.state_update.quest_updates:
            if isinstance(qu, str):
                response.narrative += f"\n\n[QUEST] {qu}"

        # 7. Persist logs
        turn_num = story_repo.get_next_turn_number(world_id)
        story_repo.add_log(world_id, turn_num, "player",   action)
        story_repo.add_log(world_id, turn_num, "narrator", response.narrative)

        return response

    # ── Private ───────────────────────────────────────────────────────────────

    def _run_summarisation(self, world_id: int):
        logs    = story_repo.get_all_raw_logs(world_id)
        summary = self.client.summarize(logs)
        story_repo.archive_and_replace_with_summary(world_id, summary)

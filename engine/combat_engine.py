from dataclasses import dataclass, field
from db import player_repo, world_repo
from llm.ollama_client import OllamaClient
from models.llm_response import LLMResponse
from engine.state_manager import StateManager
from db import story_repo
from utils import dice


@dataclass
class CombatState:
    npc_id:       int
    npc_name:     str
    npc_health:   int
    npc_max_hp:   int
    npc_strength: int
    npc_agility:  int
    npc_gold:     int
    log:          list[str] = field(default_factory=list)

    @property
    def is_over(self) -> bool:
        return self.npc_health <= 0


class CombatEngine:
    def __init__(self, client: OllamaClient, state_manager: StateManager):
        self.client  = client
        self.sm      = state_manager
        self.state: CombatState | None = None

    # ── Start / End ───────────────────────────────────────────────────────────

    def start_combat(self, npc: dict) -> str:
        self.state = CombatState(
            npc_id       = npc["id"],
            npc_name     = npc["name"],
            npc_health   = npc["health"],
            npc_max_hp   = npc.get("max_health", npc["health"]),
            npc_strength = npc["strength"],
            npc_agility  = npc["agility"],
            npc_gold     = npc["gold"],
        )
        return f"⚔ Combat begins with {npc['name']}! (HP {npc['health']})"

    def end_combat(self, player_id: int, world_id: int) -> str:
        if not self.state:
            return ""
        gold_loot = self.state.npc_gold // 2
        player_repo.add_item(player_id, f"{self.state.npc_name}'s Drop", "misc")
        new_gold = player_repo.get_player(player_id)["gold"] + gold_loot
        player_repo.update_player_stats(player_id, gold=new_gold)
        msg = (f"✓ {self.state.npc_name} is defeated! "
               f"You loot {gold_loot} gold and a trophy item.")
        self.state = None
        return msg

    # ── Turn ──────────────────────────────────────────────────────────────────

    def process_combat_turn(self, world_id: int, player_id: int,
                             action: str) -> tuple[LLMResponse, bool]:
        """
        Resolve one combat turn.  Returns (LLMResponse, combat_ended).
        """
        if not self.state:
            return LLMResponse(narrative="No active combat."), True

        player = player_repo.get_player(player_id)
        world  = world_repo.get_world(world_id)

        # ── Player attack
        stat_name, stat_val = dice.determine_relevant_stat(action, player)
        p_dice   = dice.roll(stat_name, stat_val, difficulty=12)
        p_damage = dice.combat_damage(player["strength"], p_dice)
        self.state.npc_health = max(0, self.state.npc_health - p_damage)

        # ── NPC counter-attack (always hits unless player dodges)
        n_dice    = dice.roll("agility", player["agility"], difficulty=10)
        n_damage  = 0 if n_dice.success else dice.combat_damage(self.state.npc_strength,
                                                                  dice.roll("strength", self.state.npc_strength))
        new_hp    = max(1, player["health"] - n_damage)   # narrative-only, no permadeath
        player_repo.update_player_stats(player_id, health=new_hp)

        # ── Log
        log_line = (f"T{len(self.state.log)+1}: You deal {p_damage} dmg "
                    f"({p_dice.to_prompt_string()}). "
                    f"{self.state.npc_name} deals {n_damage} back.")
        self.state.log.append(log_line)

        # ── LLM narrate
        npc_dict = {
            "name": self.state.npc_name, "health": self.state.npc_health,
            "max_health": self.state.npc_max_hp,
            "strength": self.state.npc_strength, "agility": self.state.npc_agility,
        }
        response = self.client.send_combat_turn(
            player, npc_dict, action, p_dice.to_prompt_string(),
            p_damage, n_damage, "\n".join(self.state.log[-5:]),
        )

        # ── Log to story
        turn_num = story_repo.get_next_turn_number(world_id)
        story_repo.add_log(world_id, turn_num, "player",   action)
        story_repo.add_log(world_id, turn_num, "narrator", response.narrative)

        # ── Check end
        combat_ended = self.state.is_over
        if combat_ended:
            end_msg = self.end_combat(player_id, world_id)
            response.narrative += f"\n\n{end_msg}"

        return response, combat_ended

    @property
    def in_combat(self) -> bool:
        return self.state is not None

    @property
    def combat_state(self) -> CombatState | None:
        return self.state

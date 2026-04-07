import json
import re
import requests
from pydantic import ValidationError

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from models.world import WorldSeed
from models.llm_response import LLMResponse, StateUpdate
import llm.prompt_templates as T


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model    = model

    # ── Raw API ───────────────────────────────────────────────────────────────

    def _call(self, system: str, user: str, json_mode: bool = True) -> str:
        # Note: We are deliberately disabling Ollama's format="json" because 
        # it forces strict grammar-based sampling which can slow generation 
        # down by 10x-100x for complex nested JSON on 7B models.
        # We rely on the prompt instructing the model to return JSON only.
        print(f"--- Sending request to Ollama ({self.model})...", flush=True)
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 2048}
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            print(f"--- Response received from Ollama (status: {resp.status_code})", flush=True)
            return resp.json()["message"]["content"]
        except requests.exceptions.Timeout:
            print("--- ERROR: Ollama request timed out!", flush=True)
            raise Exception("Ollama timed out. Check if your model is already loaded or if your hardware is too slow.")
        except requests.exceptions.ConnectionError:
            print("--- ERROR: Could not connect to Ollama!", flush=True)
            raise Exception(f"Connection to Ollama failed. Is Ollama running at {self.base_url}?")
        except Exception as e:
            print(f"--- ERROR: {e}", flush=True)
            raise

    def _parse_json(self, text: str) -> dict:
        """Parse JSON, stripping markdown code fences or preambles if present."""
        text = text.strip()
        
        # 1. Look for JSON inside markdown fences (greedy match for the content)
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        
        # 2. Find the outermost braces in the entire text
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
            
        # 3. Final attempt: direct parse of the stripped text
        return json.loads(text)

    def _safe_llm_response(self, raw: str) -> LLMResponse:
        """Parse LLM output into LLMResponse, recovering gracefully on errors."""
        try:
            data = self._parse_json(raw)
            # Ensure state_update is a dict before validation
            if "state_update" not in data or not isinstance(data["state_update"], dict):
                data["state_update"] = {}
            return LLMResponse(**data)
        except (json.JSONDecodeError, ValidationError, Exception):
            # Fallback: treat entire raw text as narrative
            return LLMResponse(narrative=raw[:1000] if raw else "The world holds its breath…")

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_world(self, world_name: str, theme: str, scale: str, custom_prompt: str = "") -> WorldSeed:
        raw  = self._call(T.WORLD_GEN_SYSTEM, T.world_gen_user(world_name, theme, scale, custom_prompt))
        data = self._parse_json(raw)
        # Pydantic validation with graceful defaults
        try:
            return WorldSeed(**data)
        except ValidationError:
            # Return minimal seed to prevent crash
            data.setdefault("lore_summary",      "A mysterious world awaits.")
            data.setdefault("starting_location", "The Crossroads")
            data.setdefault("factions",    [])
            data.setdefault("npcs",        [])
            data.setdefault("relationships",[])
            return WorldSeed(**data)

    def send_turn(self, player: dict, world: dict, active_quest: dict | None,
                  action: str, dice_str: str, story_context: str,
                  location: dict | None = None, rules: dict | None = None,
                  npc_context: str = "") -> LLMResponse:
        user = T.turn_user(player, world, active_quest, action, dice_str, story_context,
                           location=location, rules=rules, npc_context=npc_context)
        raw  = self._call(T.TURN_SYSTEM, user)
        return self._safe_llm_response(raw)

    def send_combat_turn(self, player: dict, npc: dict, action: str,
                         dice_str: str, player_damage: int, npc_damage: int,
                         combat_log: str) -> LLMResponse:
        user = T.combat_user(player, npc, action, dice_str,
                              player_damage, npc_damage, combat_log)
        raw  = self._call(T.COMBAT_SYSTEM, user)
        return self._safe_llm_response(raw)

    def generate_quest(self, world: dict, factions: list, npcs: list) -> dict:
        user = T.quest_gen_user(world, factions, npcs)
        raw  = self._call(T.QUEST_GEN_SYSTEM, user)
        try:
            return self._parse_json(raw)
        except Exception:
            return {
                "title":       "The Unknown Path",
                "description": "A quest shrouded in mystery.",
                "objective":   "Explore the world and uncover its secrets.",
                "hints":       ["Talk to locals.", "Search hidden areas."],
                "reward_gold": 40,
                "reward_items": [],
            }

    def summarize(self, logs: list[dict]) -> str:
        user = T.summarise_user(logs)
        return self._call(T.SUMMARISE_SYSTEM, user, json_mode=False)

    def generate_intro(self, player_name: str, world: dict, quest: dict) -> str:
        """Generate a grand opening narration for a new world."""
        system = T.INTRO_SYSTEM
        user = T.intro_user(player_name, world, quest)
        return self._call(system, user, json_mode=False)

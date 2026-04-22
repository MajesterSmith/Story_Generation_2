from config import SCALE_CONFIG

# ─────────────────────────────────────────────────────────────────────────────
# World Generation
# ─────────────────────────────────────────────────────────────────────────────

WORLD_GEN_SYSTEM = """You are the world-builder AI for a text RPG called Chronos.
Your task is to generate a rich, immersive world from a theme, name, and scale.
You must also define a logical geography (map) and a set of fundamental world laws.
Return ONLY valid JSON — no markdown, no prose, no explanation.
"""

def world_gen_user(world_name: str, theme: str, scale: str, custom_prompt: str = "") -> str:
    cfg = SCALE_CONFIG[scale]
    n_factions = cfg["factions"]
    npc_min    = cfg["npcs_min"]
    npc_max    = cfg["npcs_max"]
    
    prompt_section = ""
    if custom_prompt:
        prompt_section = f"\nAdditional World Details Provided by User:\n{custom_prompt}\n"

    return f"""Generate a {scale} world called "{world_name}" with a {theme} theme.
{prompt_section}
Requirements:
- {n_factions} unique factions
- {npc_min}–{npc_max} named NPCs
- 3–5 unique locations (settlements, landmarks, or wilderness)
- A set of world connections (which location connects to which)
- Fundamental World Rules (Magic level, Tech level, and 3-5 specific laws/taboos)
- Each NPC may optionally have 1–3 shop items
- Rich lore summary (3–5 sentences)

Return this exact JSON structure:
{{
  "world_name": "{world_name}",
  "theme": "{theme}",
  "lore_summary": "...",
  "starting_location": "Name of one location from the list below",
  "rules": {{
    "magic_level": "Low/Medium/High/Wild/None",
    "tech_level": "Primitive/Medieval/Industrial/Futuristic",
    "laws": ["Law 1", "Law 2"]
  }},
  "locations": [
    {{"name": "...", "description": "vivid detail", "type": "settlement/wilderness/dungeon/landmark", "danger_level": 1}}
  ],
  "connections": [
    {{"from_location": "...", "to_location": "...", "description": "e.g. A winding mountain path"}}
  ],
  "factions": [
    {{"name": "...", "description": "...", "traits": ["..."]}}
  ],
  "npcs": [
    {{
      "name": "...", "description": "...", "faction_name": "...",
      "traits": ["..."],
      "strength": 10, "intelligence": 10, "agility": 10,
      "health": 50, "gold": 20,
      "shop_items": [
        {{"name": "...", "type": "...", "price": 10, "properties": {{}}}}
      ]
    }}
  ],
  "relationships": [
    {{"source_name": "...", "target_name": "...", "relationship": "Enemy", "weight": 0.8}}
  ]
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Narrative Turn
# ─────────────────────────────────────────────────────────────────────────────

TURN_SYSTEM = """You are the omniscient narrator of Chronos, a text RPG.
Narrate story events vividly in second person ("You...").
Your narration must be a medium-sized paragraph (3-6 sentences).
Focus on:
- Lore-heavy descriptions of the environment and atmosphere.
- Weaving the current quest objective into the prose.
- Responding appropriately to the player's action and the dice result.
- Keep one clear main thread. Every turn should either advance, complicate, or reveal something directly connected to the active quest or an existing long-term beat.
- Avoid introducing unrelated side plots unless they clearly reinforce the main thread.

=== DICE & FAILURE RULES ===
1. A dice roll result is provided — honour it exactly.
2. If it says FAILURE, the action must fail or have a negative cost.
3. Choose one of these failure modes:
   - COMPLICATION: The action barely succeeds, but a new threat appears or a resource is damaged.
   - COST: The action fails, and you lose HP, Gold, or an Item.
   - HARD STOP: The path is totally blocked; you must find another way.
4. Reflect these costs in the "state_update" JSON fields.

=== SOCIAL & MEMORY RULES ===
1. If the player interacts with an NPC/Faction, update relationship changes (-20 to +20).
2. "npc_memory_summary": A 1-sentence summary for the NPC to remember.
3. "important_beat": If a major, world-changing, or plot-defining event occurred (e.g. death of a key NPC, finishing a major quest, discovery of a legendary artifact), provide a 1-sentence summary here. This will be stored in long-term memory.
4. "candidate_beats": Always provide 1-3 focused candidate beats for the main thread. Each candidate must be a short summary with a beat type and importance.

Return ONLY valid JSON — no markdown, no prose outside the narrative field.
"""

def turn_user(player: dict, world: dict, active_quest: dict | None,
              action: str, dice_str: str, story_context: str,
              location: dict | None = None, rules: dict | None = None,
              npc_context: str = "", story_beats: str = "") -> str:
    quest_txt = "None"
    if active_quest:
        quest_txt = (f"{active_quest['title']}: {active_quest['objective']} "
                     f"(Hints: {', '.join(active_quest.get('hints', []))})")
    return f"""=== WORLD ===
Name: {world['name']} | Theme: {world['theme']}
Lore: {world['lore_summary']}
Rules: Magic:{rules.get('magic_level', 'Unknown')} | Tech:{rules.get('tech_level', 'Unknown')}
Laws: {', '.join(rules.get('laws', [])) if rules else 'None'}

=== MAJOR STORY SO FAR ===
{story_beats if story_beats else "The journey has just begun."}

=== LOCATION ===
Current: {location['name'] if location else player['current_location']}
Type: {location['type'] if location else 'Unknown'} | Danger: {location['danger_level'] if location else 1}
Description: {location['description'] if location else 'No description available.'}

=== PLAYER ===
Name: {player['name']} | Location: {player['current_location']}
STR:{player['strength']} INT:{player['intelligence']} AGI:{player['agility']}
HP:{player['health']}/{player['max_health']}  Gold:{player['gold']}

=== ACTIVE QUEST ===
{quest_txt}

=== RECENT STORY ===
{story_context}

=== NPC CONTEXT ===
{npc_context}

=== DICE CHECK ===
{dice_str}

=== PLAYER ACTION ===
{action}

Return this JSON:
{{
  "narrative": "A rich 3-6 sentence paragraph containing lore, quest integration, and sensory details.",
  "state_update": {{
    "stat_changes": {{}},
    "items_gained": [],
    "items_lost": [],
    "gold_change": 0,
    "quest_updates": [],
    "relationship_changes": [],
    "npc_interacted_name": null,
    "npc_relationship_change": 0,
    "npc_memory_summary": null,
    "faction_interacted_name": null,
    "faction_relationship_change": 0,
    "important_beat": null
  }},
  "candidate_beats": [
    {{"summary": "One focused beat tied to the current quest.", "beat_type": "main", "importance": 7, "weight": 1.0, "tags": ["quest"]}},
    {{"summary": "A complication that raises the stakes.", "beat_type": "complication", "importance": 5, "weight": 0.8, "tags": ["stakes"]}}
  ],
  "suggested_choices": ["choice 1", "choice 2", "choice 3"],
  "combat_outcome": null,
  "new_quest": null,
  "npc_dialogue": null,
  "trade_offer": null
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Background World Events
# ─────────────────────────────────────────────────────────────────────────────

WORLD_EVENT_SYSTEM = """You are the background simulator for Chronos.
Generate a significant world event that happens while the player is occupied.
Events should involve Faction power shifts, NPC movements, or natural/political disasters.
Return ONLY valid JSON.
"""

def world_event_user(world: dict, factions: list, npcs: list, beats: str) -> str:
    f_list = [f"{f['name']}: {f['description']} (Rep: {f['relationship_score']})" for f in factions]
    n_list = [n['name'] for n in npcs[:10]]
    return f"""World: {world['name']} ({world['theme']})
Lore: {world['lore_summary']}
Major History: {beats}

Factions: {', '.join(f_list)}
Notable NPCs: {', '.join(n_list)}

Generate a background event. Return:
{{
  "event_narration": "A 2-3 sentence description of what happened in the world.",
  "state_update": {{
    "faction_interacted_name": "...",
    "faction_relationship_change": 0,
    "npc_interacted_name": "...",
    "npc_relationship_change": 0,
    "important_beat": "A 1-sentence summary for long-term memory."
  }}
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Combat Turn
# ─────────────────────────────────────────────────────────────────────────────

COMBAT_SYSTEM = """You are the combat narrator for Chronos.
The dice check determines the attack outcome — honour it exactly.
Narrate combat in vivid, descriptive second-person prose (3-5 sentences). 
Incorporate the surrounding environment and the weight of the battle.
Return ONLY valid JSON.
"""

def combat_user(player: dict, npc: dict, action: str, dice_str: str,
                player_damage: int, npc_damage: int, combat_log: str) -> str:
    return f"""=== COMBATANTS ===
Player: {player['name']} HP:{player['health']}/{player['max_health']} STR:{player['strength']} AGI:{player['agility']}
Enemy:  {npc['name']}   HP:{npc['health']}/{npc['max_health']}   STR:{npc['strength']} AGI:{npc['agility']}

=== COMBAT LOG ===
{combat_log}

=== DICE CHECK ===
{dice_str}

=== PLAYER ACTION ===
{action}

=== COMPUTED RESULTS ===
Player dealt {player_damage} damage | Enemy dealt {npc_damage} damage back

Return this JSON:
{{
  "narrative": "A descriptive 3-5 sentence combat paragraph.",
  "state_update": {{
    "stat_changes": {{}}, "items_gained": [], "items_lost": [], "gold_change": 0,
    "quest_updates": [], "relationship_changes": []
  }},
  "suggested_choices": ["attack again", "use item", "flee"],
  "combat_outcome": "HIT"
}}

combat_outcome must be one of: HIT, MISS, CRITICAL, DODGE"""


# ─────────────────────────────────────────────────────────────────────────────
# Opening Narration
# ─────────────────────────────────────────────────────────────────────────────

INTRO_SYSTEM = """You are the opening narrator for Chronos, a text RPG.
Your task is to set the scene for a brand new adventure.
Write a grand, atmospheric 4-6 sentence opening narration in second person ("You...").
Include details about the world's theme, lore summary, and the specific starting location.
Foreshadow the initial quest objective slightly.
Return ONLY plain text. No markdown, no JSON.
"""

def intro_user(player_name: str, world: dict, quest: dict) -> str:
    return f"""World: {world['name']} ({world['theme']})
Lore: {world['lore_summary']}
Starting Location: {world['starting_location']}
Initial Quest: {quest['title']} - {quest['objective']}
Player Name: {player_name}

Write the opening narration for {player_name}'s first moments in this world."""


# ─────────────────────────────────────────────────────────────────────────────
# Quest Generation
# ─────────────────────────────────────────────────────────────────────────────

QUEST_GEN_SYSTEM = """You generate quests for a text RPG called Chronos.
Create a single, compelling quest appropriate to the world.
Return ONLY valid JSON.
"""

def quest_gen_user(world: dict, factions: list, npcs: list) -> str:
    npc_names     = [n["name"] for n in npcs[:6]]
    faction_names = [f["name"] for f in factions]
    return f"""World: {world['name']} ({world['theme']})
Lore: {world['lore_summary']}
Factions: {', '.join(faction_names)}
Notable NPCs: {', '.join(npc_names)}

Generate one quest. Return:
{{
  "title": "...",
  "description": "2-sentence quest background",
  "objective": "single clear goal sentence",
  "hints": ["hint 1", "hint 2"],
  "reward_gold": 50,
  "reward_items": ["item name"]
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Summarisation
# ─────────────────────────────────────────────────────────────────────────────

SUMMARISE_SYSTEM = """You are a story archivist for a text RPG.
Summarise the story events below in ≤300 words.
Preserve: key plot moments, NPC names introduced, items gained/lost, stat changes, quest progress.
Write in past tense, second person ("You discovered...").
Return ONLY plain text — no JSON.
"""

def summarise_user(logs: list[dict]) -> str:
    lines = []
    for log in logs:
        prefix = log["role"].upper()
        lines.append(f"[{prefix}] {log['content']}")
    return "\n".join(lines)

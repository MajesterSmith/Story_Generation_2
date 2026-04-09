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

TURN_SYSTEM = """You are the master narrator of Chronos, an immersive text RPG.
Your goal is to provide rich, cinematic, and atmospheric storytelling in second person ("You...").

=== NARRATION GUIDELINES ===
1. LENGTH: Write 2-3 detailed paragraphs (approx. 8-15 sentences).
2. SENSORY PILLARS: Interweave details of sight (shadows, light), sound (distant echoes, footsteps), smell (damp earth, metallic blood), and emotional resonance.
3. FORMATTING: Use Markdown to enhance readability:
   - **Bold** for NPC names, locations, and important items.
   - *Italics* for internal thoughts, whispers, or subtle environmental cues.
4. LORE: Weave the current quest objective and world rules naturally into the prose.
5. CONSEQUENCE: Respect the dice roll — if it says FAILURE, describe the struggle or the setback with weight.

=== SOCIAL SIMULATION RULES ===
1. Identify if the player is interacting with a specific NPC or Faction.
2. If yes, update their "npc_relationship_change" or "faction_relationship_change" (range -20 to +20).
3. If a SIGNIFICANT event occurs (betrayal, gift, life-saving, grave insult), provide a 1-sentence "npc_memory_summary".
4. Adjust NPC dialogue style based on their current relationship score (provided in context).

Track all state changes carefully and return them in the JSON.
Return ONLY valid JSON. The 'narrative' field should contain the full formatted story.
"""

def turn_user(player: dict, world: dict, active_quest: dict | None,
              action: str, dice_str: str, story_context: str,
              location: dict | None = None, rules: dict | None = None,
              npc_context: str = "") -> str:
    quest_txt = "None"
    if active_quest:
        quest_txt = (f"{active_quest['title']}: {active_quest['objective']} "
                     f"(Hints: {', '.join(active_quest.get('hints', []))})")
    return f"""=== WORLD ===
Name: {world['name']} | Theme: {world['theme']}
Lore: {world['lore_summary']}
Rules: Magic:{rules.get('magic_level', 'Unknown')} | Tech:{rules.get('tech_level', 'Unknown')}
Laws: {', '.join(rules.get('laws', [])) if rules else 'None'}

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
  "narrative": "A rich, multi-paragraph story (8-15 sentences) with sensory details and Markdown formatting.",
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
    "faction_relationship_change": 0
  }},
  "suggested_choices": ["choice 1", "choice 2", "choice 3"],
  "combat_outcome": null,
  "new_quest": null,
  "npc_dialogue": null,
  "trade_offer": null
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Combat Turn
# ─────────────────────────────────────────────────────────────────────────────

COMBAT_SYSTEM = """You are the lead combat choreographer for Chronos.
The dice check determines the attack outcome — honour it precisely with descriptive weight.

=== COMBAT NARRATION ===
1. LENGTH: 2-3 vivid paragraphs.
2. SENSORY: Describe the whistle of steel, the spray of gravel underfoot, the thud of impacts, and the exhaustion of the combatants.
3. FORMATTING: Use **Bold** for damage-related events or critical names. Use *Italics* for the adrenaline and instincts of the player.
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

INTRO_SYSTEM = """You are the opening narrator for Chronos, a grand text RPG.
Your task is to set the stage for an epic journey.

=== INTRO GUIDELINES ===
1. STYLE: Grand, atmospheric, and cinematic.
2. STRUCTURE: Write 3 paragraphs.
   - Paragraph 1: The world at large and its ancient history/lore.
   - Paragraph 2: The immediate surroundings and the atmosphere of the starting location.
   - Paragraph 3: The player's arrival and the weight of the task ahead (*foreshadowing*).
3. FORMATTING: Use **Bold** for the World Name and Location.
4. TEXT ONLY: Return ONLY plain text with Markdown formatting. No JSON.
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

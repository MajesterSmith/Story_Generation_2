import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / "chronos.db")

# --- Ollama ---
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_TIMEOUT = 120  # seconds

# --- Context / Summarization ---
SUMMARIZE_TOKEN_THRESHOLD = 3000
TOKEN_ESTIMATION_CHARS_PER_TOKEN = 4  # ~4 chars ≈ 1 token

# --- World Scale ---
SCALE_CONFIG = {
    "Small":  {"factions": 2, "npcs_min": 5,  "npcs_max": 8},
    "Medium": {"factions": 4, "npcs_min": 12, "npcs_max": 18},
    "Large":  {"factions": 7, "npcs_min": 25, "npcs_max": 35},
}

# --- Player Defaults ---
DEFAULT_STRENGTH     = 10
DEFAULT_INTELLIGENCE = 10
DEFAULT_AGILITY      = 10
DEFAULT_HEALTH       = 100
DEFAULT_GOLD         = 50

# --- Dice ---
DICE_SIDES        = 20
DEFAULT_DIFFICULTY = 12   # DC (Difficulty Class)

# --- UI ---
TYPEWRITER_DELAY_MS = 5   # milliseconds between characters

# --- Trading ---
NPC_BUY_RATE = 0.5   # NPCs buy player items at 50% listed value

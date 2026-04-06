import random
from models.llm_response import DiceResult
from config import DICE_SIDES, DEFAULT_DIFFICULTY

_PHYSICAL  = {"attack","push","climb","break","punch","kick","lift","carry",
               "bash","smash","swing","stab","cut","slash","force","wrestle","throw"}
_MENTAL    = {"cast","read","study","examine","decipher","magic","spell",
               "persuade","negotiate","analyze","identify","craft","brew","inscribe","convince"}
_AGILITY   = {"dodge","sneak","run","jump","hide","flee","pick","lock",
               "tumble","roll","duck","evade","steal","shoot","aim","sprint"}


def _modifier(stat: int) -> int:
    return (stat - 10) // 2


def roll(stat_name: str, stat_value: int, difficulty: int = DEFAULT_DIFFICULTY) -> DiceResult:
    base    = random.randint(1, DICE_SIDES)
    mod     = _modifier(stat_value)
    total   = base + mod
    return DiceResult(
        stat_used=stat_name,
        stat_value=stat_value,
        roll=base,
        modifier=mod,
        total=total,
        threshold=difficulty,
        success=(total >= difficulty),
    )


def determine_relevant_stat(action: str, player: dict) -> tuple[str, int]:
    words = set(action.lower().split())
    if words & _PHYSICAL:
        return "strength",     player.get("strength",     10)
    if words & _MENTAL:
        return "intelligence", player.get("intelligence", 10)
    if words & _AGILITY:
        return "agility",      player.get("agility",      10)
    # Default: use the player's highest stat
    stats = {
        "strength":     player.get("strength",     10),
        "intelligence": player.get("intelligence", 10),
        "agility":      player.get("agility",      10),
    }
    best = max(stats, key=lambda k: stats[k])
    return best, stats[best]


def combat_damage(attacker_strength: int, dice_result: DiceResult) -> int:
    """Return damage dealt based on dice outcome and attacker strength."""
    if not dice_result.success:
        return 0
    base = random.randint(1, 6)
    bonus = _modifier(attacker_strength)
    if dice_result.roll == DICE_SIDES:          # natural 20 → critical
        return max(1, (base + bonus) * 2)
    return max(1, base + bonus)

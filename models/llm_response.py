from pydantic import BaseModel, Field
from typing import Optional


class DiceResult(BaseModel):
    stat_used: str
    stat_value: int
    roll: int
    modifier: int
    total: int
    threshold: int
    success: bool

    def to_prompt_string(self) -> str:
        sign = "+" if self.modifier >= 0 else ""
        outcome = "SUCCESS" if self.success else "FAILURE"
        return (
            f"[DICE CHECK: {self.stat_used.upper()}({self.stat_value}) "
            f"→ Roll {self.roll}{sign}{self.modifier}={self.total} "
            f"vs DC{self.threshold} → {outcome}]"
        )


class StateUpdate(BaseModel):
    stat_changes: dict[str, int] = Field(default_factory=dict)
    items_gained: list[str] = Field(default_factory=list)
    items_lost: list[str] = Field(default_factory=list)
    gold_change: int = 0
    quest_updates: list[dict | str] = Field(default_factory=list)
    # [{"source": "NPC_Name", "target": "Faction_Name", "type": "Enemy", "weight": 0.8}]
    relationship_changes: list[dict] = Field(default_factory=list)
    
    # NPC Social Updates
    npc_interacted_name: Optional[str] = None
    npc_relationship_change: int = 0
    npc_memory_summary: Optional[str] = None
    
    # Faction Social Updates
    faction_interacted_name: Optional[str] = None
    faction_relationship_change: int = 0

    # Long-term Memory
    important_beat: Optional[str] = None


class LLMResponse(BaseModel):
    narrative: str = ""
    state_update: StateUpdate = Field(default_factory=StateUpdate)
    suggested_choices: list[str] = Field(default_factory=list)
    combat_outcome: Optional[str] = None   # HIT | MISS | CRITICAL | DODGE
    new_quest: Optional[dict] = None
    npc_dialogue: Optional[str] = None
    trade_offer: Optional[dict] = None
    
    # Can also be set at the top level for convenience
    important_beat: Optional[str] = None

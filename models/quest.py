from pydantic import BaseModel, Field
from typing import Optional


class QuestModel(BaseModel):
    id: Optional[int] = None
    world_id: int
    player_id: int
    title: str
    description: str
    objective: str
    status: str = "ACTIVE"   # INACTIVE | ACTIVE | COMPLETED | FAILED
    hints: list[str] = []
    reward_gold: int = 0
    reward_items: list[str] = []

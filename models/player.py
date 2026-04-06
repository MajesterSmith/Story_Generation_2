from pydantic import BaseModel, Field
from typing import Optional


class InventoryItem(BaseModel):
    id: Optional[int] = None
    item_name: str
    item_type: str = "misc"   # weapon | armor | consumable | misc
    quantity: int = 1
    properties: dict = {}


class PlayerModel(BaseModel):
    id: Optional[int] = None
    world_id: int
    name: str
    strength: int = 10
    intelligence: int = 10
    agility: int = 10
    health: int = 100
    max_health: int = 100
    gold: int = 50
    current_location: str = ""
    inventory: list[InventoryItem] = []

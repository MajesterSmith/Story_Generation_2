from pydantic import BaseModel, Field
from typing import Optional


class FactionModel(BaseModel):
    name: str
    description: str
    traits: list[str] = []


class NPCModel(BaseModel):
    name: str
    description: str = ""
    faction_name: Optional[str] = None
    traits: list[str] = []
    strength: int = Field(default=10, ge=1, le=20)
    intelligence: int = Field(default=10, ge=1, le=20)
    agility: int = Field(default=10, ge=1, le=20)
    health: int = Field(default=50, ge=1, le=200)
    gold: int = Field(default=10, ge=0)
    shop_items: list[dict] = []


class RelationshipModel(BaseModel):
    source_name: str
    target_name: str
    relationship: str = "Neutral"
    weight: float = Field(default=0.5, ge=0.0, le=1.0)


class LocationModel(BaseModel):
    name: str
    description: str
    type: str = "settlement"  # settlement | wilderness | dungeon | landmark
    danger_level: int = Field(default=1, ge=1, le=10)


class ConnectionModel(BaseModel):
    from_location: str
    to_location: str
    description: str = "A path connects these two places."


class WorldRulesModel(BaseModel):
    magic_level: str = "Medium"      # None | Low | Medium | High | Wild
    tech_level: str = "Medieval"     # Primitive | Medieval | Industrial | Futuristic
    laws: list[str] = []             # List of fundamental world laws/taboos


class WorldSeed(BaseModel):
    world_name: str
    theme: str
    lore_summary: str
    starting_location: str
    factions: list[FactionModel] = []
    npcs: list[NPCModel] = []
    relationships: list[RelationshipModel] = []
    locations: list[LocationModel] = []
    connections: list[ConnectionModel] = []
    rules: WorldRulesModel = Field(default_factory=WorldRulesModel)

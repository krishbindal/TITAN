from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class CardMetadata(BaseModel):
    id: int
    name: str
    rarity: str
    cost: int = Field(ge=0)
    type: Literal["troop", "building", "spell"]
    arena: int
    is_evolution: bool = False
    is_champion: bool = False

class CombatStats(BaseModel):
    hp: int = Field(ge=0)
    damage: int = Field(ge=0)
    dps: int = Field(ge=0)
    hit_speed: float = Field(ge=0.0)
    range: float = Field(ge=0.0)
    speed_numeric: int = Field(ge=0)
    speed_class: str
    target_type: Literal["ground", "air_ground", "building", "any"]
    targets_air: bool
    targets_ground: bool
    splash_radius: float = Field(ge=0.0)
    projectile_speed: Optional[float] = None
    deploy_time: float = Field(ge=0.0)
    count: int = Field(ge=1)

class Mechanics(BaseModel):
    shield_hp: int = 0
    death_damage: int = 0
    charge_damage: int = 0
    stun_duration: float = 0.0
    knockback: bool = False
    jumps_river: bool = False

class AITags(BaseModel):
    roles: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    kiting_priority: int = 0

class CardModel(BaseModel):
    metadata: CardMetadata
    combat: CombatStats
    mechanics: Mechanics
    ai_tags: AITags

    @property
    def cost(self) -> int:
        return self.metadata.cost

    @property
    def name(self) -> str:
        return self.metadata.name

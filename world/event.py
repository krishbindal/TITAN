from enum import Enum


class EventType(Enum):

    TROOP_SPAWN = "Troop Spawn"

    TROOP_DIED = "Troop Died"

    TROOP_MOVED = "Troop Moved"

    SPELL_CAST = "Spell Cast"

    BUILDING_PLACED = "Building Placed"

    TOWER_DAMAGE = "Tower Damage"


class Event:

    def __init__(self, event_type, time, description):

        self.event_type = event_type

        self.time = time

        self.description = description

    def __str__(self):

        return f"[{self.time:.2f}] {self.event_type.value}: {self.description}"

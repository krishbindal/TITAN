from enum import Enum


class Action(Enum):

    IDLE = "Idle"

    MOVING = "Moving"

    ATTACKING = "Attacking"

    DEAD = "Dead"

    SPAWNING = "Spawning"

    UNKNOWN = "Unknown"

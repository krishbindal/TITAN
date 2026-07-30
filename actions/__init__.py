from enum import Enum


class Action(Enum):

    UNKNOWN = "Unknown"

    SPAWNING = "Spawning"

    MOVING = "Moving"

    ATTACKING = "Attacking"

    IDLE = "Idle"

    DEAD = "Dead"

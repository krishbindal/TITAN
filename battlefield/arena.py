from enum import Enum


class Side(Enum):
    BLUE = "Blue"
    RED = "Red"


class Lane(Enum):
    LEFT = "Left"
    RIGHT = "Right"


class Region(Enum):
    BLUE_SIDE = "Blue Side"
    RED_SIDE = "Red Side"
    RIVER = "River"

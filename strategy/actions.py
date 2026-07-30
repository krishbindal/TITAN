from enum import Enum
from dataclasses import dataclass


class Action(Enum):

    DO_NOTHING = 0

    PLAY_CARD = 1

    WAIT = 2


@dataclass
class ActionCommand:
    action: Action
    card_to_play: str = None
    target_x: int = None
    target_y: int = None

    @property
    def name(self):
        if self.card_to_play:
            return f"{self.action.name} ({self.card_to_play})"
        return self.action.name

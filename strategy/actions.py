from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Action(Enum):

    DO_NOTHING = 0

    PLAY_CARD = 1

    WAIT = 2


@dataclass
class ActionCommand:
    action: Action
    card_to_play: Optional[str] = None
    target_x: Optional[int] = None
    target_y: Optional[int] = None

    @property
    def name(self):
        if self.card_to_play:
            return f"{self.action.name} ({self.card_to_play})"
        return self.action.name

class BattleState:

    def __init__(self):

        self.events = []

        self.active_pushes = []

        self.danger_level = 0

        self.player_advantage = 0

    def add_event(self, event):

        self.events.append(event)

    def __str__(self):

        return (
            f"Events: {len(self.events)}\n"
            f"Danger: {self.danger_level}\n"
            f"Advantage: {self.player_advantage}"
        )

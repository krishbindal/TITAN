class GameState:

    def __init__(self):

        self.time = 0.0

        self.troops = []

        self.hand = []

        self.events = []

    def add_troop(self, troop):

        self.troops.append(troop)

    def add_card_to_hand(self, card_name):

        # Avoid duplicates in hand (sometimes YOLO detects multiple boxes for one card)
        if card_name not in self.hand:
            self.hand.append(card_name)

    def clear(self):

        self.troops.clear()

        self.hand.clear()

        self.events.clear()

    def __str__(self):

        output = []

        output.append("=" * 50)

        output.append("GAME STATE")

        output.append("=" * 50)

        output.append(f"Hand: {', '.join(self.hand)}")

        output.append("")

        output.append(f"Troops: {len(self.troops)}")

        output.append("")

        for troop in self.troops:

            output.append(str(troop))

        return "\n".join(output)

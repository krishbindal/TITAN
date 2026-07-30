import json
import os

from knowledge.card import CardModel


class CardDatabase:

    def __init__(self):

        # Resolve path relative to this file
        json_path = os.path.join(os.path.dirname(__file__), "titan_cards.json")

        with open(json_path) as f:
            raw = json.load(f)

        self.cards = {}

        for name, data in raw.items():
            self.cards[name] = CardModel(**data)

    def get(self, name):
        """
        Retrieves the CardModel for a given card name.
        Returns None if not found.
        """
        return self.cards.get(name)

    def all_cards(self):
        return list(self.cards.values())

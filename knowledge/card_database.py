import json
import os

from knowledge.card import Card


class CardDatabase:

    def __init__(self):

        # Resolve path relative to this file, not the working directory
        json_path = os.path.join(os.path.dirname(__file__), "cards.json")

        with open(json_path) as f:
            raw = json.load(f)

        self.cards = {}

        for name, data in raw.items():
            self.cards[name] = Card(
                name=data.get("name", name),
                cost=data.get("cost"),
                card_type=data.get("type"),
                target=data.get("target"),
                speed=data.get("speed"),
                range=data.get("range"),
                hp=data.get("hp", 0),
                damage=data.get("damage", 0),
                hit_speed=data.get("hit_speed", 1.0),
                count=data.get("count", 1),
                deploy_time=data.get("deploy_time", 1.0),
            )

    def get(self, name):
        return self.cards.get(name)

    def all_cards(self):
        return list(self.cards.values())

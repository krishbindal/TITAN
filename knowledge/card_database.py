import json
import os

from knowledge.card import CardModel, CardMetadata, CombatStats, Mechanics, AITags


class CardDatabase:
    # Maps YOLO strings (card_*, enemy_*, ally_*, or plain) to canonical db keys
    NORMALIZATION_MAP = {
        'valk': 'valkyrie',
        'barb': 'barbarians',
        'bats': 'bats',
        'bat': 'bats',
        'minion': 'minions',
        'minions': 'minions',
        'skeleton': 'skeletons',
        'skeletons': 'skeletons',
        'elite_barb': 'elite_barbarians',
        'wall_breaker': 'wall_breakers',
        'wall_breakers': 'wall_breakers',
        'lumber_jack': 'lumberjack',
        'snow_ball': 'snowball',
        'pig': 'royal_hogs',
        'rider': 'hog_rider',
        'stone': 'tombstone',
        'zappy': 'zappies',
        'peka': 'pekka',
        'elctro_wizard': 'electro_wizard',
        'phenix': 'phoenix',
        'gaint': 'giant',
        'guard': 'guards',
    }

    def __init__(self):
        # Resolve path relative to this file
        json_path = os.path.join(os.path.dirname(__file__), "titan_cards.json")

        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)

        self.cards = {}

        for name, data in raw.items():
            self.cards[name] = CardModel(**data)

    @classmethod
    def normalize(cls, name: str) -> str:
        name = name.replace("enemy_", "").replace("ally_", "").replace("card_", "")
        return cls.NORMALIZATION_MAP.get(name, name)

    def get(self, name):
        """
        Retrieves the CardModel for a given card name.
        Returns a generic fallback card if not found to prevent crashes.
        """
        normalized = self.normalize(name)
        if normalized in self.cards:
            return self.cards[normalized]
            
        return CardModel(
            metadata=CardMetadata(id=0, name=normalized.capitalize(), rarity="common", cost=4, type="troop", arena=1),
            combat=CombatStats(hp=1000, damage=100, dps=100, hit_speed=1.0, range=1.0, speed_numeric=60, speed_class="medium", target_type="ground", targets_air=False, targets_ground=True, splash_radius=0.0, deploy_time=1.0, count=1),
            mechanics=Mechanics(),
            ai_tags=AITags(roles=["unknown"])
        )

    def all_cards(self):
        return list(self.cards.values())

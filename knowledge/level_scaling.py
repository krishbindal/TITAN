from knowledge.card import CardModel


class LevelScaling:

    @staticmethod
    def get_stats_at_level(card: CardModel, target_level: int) -> CardModel:
        """
        Scales a card's HP and Damage to the target level.
        In Clash Royale, stats scale by +10% exactly per level.
        Base stats in the DB are at Tournament Standard (Level 11).
        """
        base_level = 11
        level_diff = target_level - base_level

        # Scale factor is 1.1 ^ level_diff
        scale_factor = 1.1**level_diff

        # Calculate new scaled stats (rounded to nearest integer as in-game)
        new_hp = round(card.combat.hp * scale_factor)
        new_damage = round(card.combat.damage * scale_factor)
        new_dps = round(card.combat.dps * scale_factor)
        
        # We must deepcopy the model so we don't accidentally mutate the master DB
        scaled_card = card.model_copy(deep=True)
        scaled_card.combat.hp = new_hp
        scaled_card.combat.damage = new_damage
        scaled_card.combat.dps = new_dps

        return scaled_card

from knowledge.card import Card


class LevelScaling:

    @staticmethod
    def get_stats_at_level(card: Card, target_level: int) -> Card:
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
        new_hp = round(card.hp * scale_factor)
        new_damage = round(card.damage * scale_factor)

        # Create a new scaled card instance
        return Card(
            name=card.name,
            cost=card.cost,
            card_type=card.card_type,
            target=card.target,
            speed=card.speed,
            range=card.range,
            hp=new_hp,
            damage=new_damage,
            hit_speed=card.hit_speed,
            count=card.count,
            deploy_time=card.deploy_time,
        )

class Card:

    def __init__(
        self,
        name,
        cost,
        card_type,
        target=None,
        speed=None,
        range=None,
        hp=0,
        damage=0,
        hit_speed=1.0,
        count=1,
        deploy_time=1.0,
    ):

        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.target = target
        self.speed = speed
        self.range = range

        # Deep Stats
        self.hp = hp
        self.damage = damage
        self.hit_speed = hit_speed
        self.count = count
        self.deploy_time = deploy_time

    @property
    def dps(self):
        if self.hit_speed > 0:
            return round(self.damage / self.hit_speed)
        return 0

    def __str__(self):
        return f"{self.name} ({self.cost} elixir) | HP: {self.hp} | DPS: {self.dps}"

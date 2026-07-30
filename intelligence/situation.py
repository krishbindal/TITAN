class Situation:

    def __init__(
        self,
        lane,
        attacker,
        troop_count,
        threat,
        estimated_elixir,
    ):
        self.lane = lane
        self.attacker = attacker
        self.troop_count = troop_count
        self.threat = threat
        self.estimated_elixir = estimated_elixir

    def __str__(self):
        return (
            f"Lane: {self.lane}\n"
            f"Attacker: {self.attacker}\n"
            f"Threat: {self.threat}\n"
            f"Troops: {self.troop_count}\n"
            f"Estimated Elixir: {self.estimated_elixir}"
        )

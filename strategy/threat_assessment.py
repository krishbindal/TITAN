"""
Threat Assessment Engine for TITAN.
Analyzes the current GameState to calculate danger levels
per lane and identify the most urgent threats.
"""

from knowledge.card_database import CardDatabase
from knowledge.level_scaling import LevelScaling
from configs.game_config import get_expected_enemy_level


class ThreatAssessment:
    """
    Evaluates the battlefield to determine:
    - Total incoming DPS per lane (left / right)
    - The single most dangerous enemy troop
    - Whether the player is under immediate pressure
    """

    # The arena center X coordinate (720px wide screen)
    ARENA_CENTER_X = 360

    # If an enemy troop is past this Y threshold, it's in "danger zone"
    # (close to the player's side of the arena)
    DANGER_ZONE_Y = 700

    def __init__(self):
        self.card_db = CardDatabase()

    def assess(self, game_state):
        """
        Analyze the game state and return a ThreatReport.

        Args:
            game_state: GameState object with .troops list

        Returns:
            ThreatReport with lane DPS, top threat, and pressure flag
        """
        left_dps = 0.0
        right_dps = 0.0
        top_threat = None
        top_threat_dps = 0.0
        enemy_count = 0
        pressure = False

        for troop in game_state.troops:

            # Only assess enemy troops
            if troop.team != "enemy":
                continue

            enemy_count += 1

            # Look up the card in our knowledge base
            # Strip 'enemy_' prefix to match database keys
            card_key = troop.name.replace("enemy_", "")
            card = self.card_db.get(card_key)

            if card is None:
                # Unknown card — estimate a moderate DPS
                troop_dps = 100.0
            else:
                # Scale to the troop's actual level if known
                level = getattr(troop, "level", None)
                if level is None:
                    level = get_expected_enemy_level()
                scaled = LevelScaling.get_stats_at_level(card, level)
                troop_dps = scaled.dps * scaled.count

            # Assign to lane based on X position
            if troop.x < self.ARENA_CENTER_X:
                left_dps += troop_dps
            else:
                right_dps += troop_dps

            # Track the single most dangerous unit
            if troop_dps > top_threat_dps:
                top_threat_dps = troop_dps
                top_threat = troop

            # Check if any enemy is in the danger zone
            if troop.y > self.DANGER_ZONE_Y:
                pressure = True

        return ThreatReport(
            left_dps=left_dps,
            right_dps=right_dps,
            top_threat=top_threat,
            enemy_count=enemy_count,
            pressure=pressure,
        )


class ThreatReport:
    """Container for the results of a threat assessment."""

    def __init__(
        self,
        left_dps=0.0,
        right_dps=0.0,
        top_threat=None,
        enemy_count=0,
        pressure=False,
    ):
        self.left_dps = left_dps
        self.right_dps = right_dps
        self.top_threat = top_threat
        self.enemy_count = enemy_count
        self.pressure = pressure

    @property
    def total_dps(self):
        return self.left_dps + self.right_dps

    @property
    def hot_lane(self):
        """Returns 'left', 'right', or 'balanced'."""
        if self.left_dps > self.right_dps * 1.5:
            return "left"
        elif self.right_dps > self.left_dps * 1.5:
            return "right"
        return "balanced"

    def __str__(self):
        threat_name = self.top_threat.name if self.top_threat else "None"
        return (
            f"Threat Report | "
            f"Left: {self.left_dps:.0f} DPS | "
            f"Right: {self.right_dps:.0f} DPS | "
            f"Hot Lane: {self.hot_lane} | "
            f"Top Threat: {threat_name} | "
            f"Pressure: {'YES' if self.pressure else 'No'}"
        )

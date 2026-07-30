import math
from knowledge.card_database import CardDatabase

class PlacementEngine:
    def __init__(self):
        self.card_db = CardDatabase()
        # Base screen dimensions
        self.center_x = 360
        self.center_y = 640
        self.bridge_y = 550
        self.center_pull_y = 750

        # Card categories for placement logic
        self.spells = {
            "log",
            "zap",
            "fireball",
            "arrows",
            "poison",
            "rocket",
            "lightning",
            "snow_ball",
        }
        self.ranged = {
            "musketeer",
            "archer",
            "magic_archer",
            "wizard",
            "electro_wizard",
            "ice_wizard",
            "fire_cracker",
            "flying_machine",
            "dart_goblin",
            "princess",
            "hunter",
        }
        self.buildings = {
            "cannon",
            "tesla",
            "inferno_tower",
            "bomb_tower",
            "tombstone",
            "goblin_cage",
            "furnace",
            "goblin_hut",
            "elixir_pump",
            "mortar",
            "xbow",
        }
        self.tanks = {
            "giant",
            "golem",
            "pekka",
            "mega_knight",
            "lava_hound",
            "royal_giant",
            "skeleton_giant",
            "goblin_giant",
        }
        self.swarms = {
            "skeleton_army",
            "minion_horde",
            "goblin_gang",
            "bats",
            "skeletons",
            "minions",
            "guards",
        }
        self.win_conditions = {
            "hog_rider",
            "ram_rider",
            "balloon",
            "goblin_barrel",
            "miner",
            "wall_breakers",
            "battle_ram",
        }

    def calculate_drop(self, card_to_play, threat_report, game_state):
        """
        Calculate optimal (x, y) coordinates to drop the card.
        """
        if not card_to_play:
            return None, None

        # --- Spatial Grid & Centroid Calculation ---
        # Instead of just looking at the top threat, we find the "center of mass" of the push
        push_x = 0
        push_y = 0
        push_count = 0
        
        for troop in game_state.troops:
            if troop.team == "enemy" and troop.y > self.bridge_y - 100:
                # If they are in our half or approaching
                if (threat_report.hot_lane == "left" and troop.x < self.center_x) or \
                   (threat_report.hot_lane == "right" and troop.x > self.center_x):
                    push_x += troop.x
                    push_y += troop.y
                    push_count += 1
                    
        if push_count > 0:
            centroid_x = int(push_x / push_count)
            centroid_y = int(push_y / push_count)
        else:
            # Fallback if no enemies on hot lane
            centroid_x, centroid_y = (180 if threat_report.hot_lane == "left" else 540), 750

        # 1. Offensive Push (No immediate pressure)
        if not threat_report.pressure or not threat_report.top_threat:
            return self._calculate_offensive_drop(card_to_play, threat_report)

        # 2. Defensive Placement (Under pressure)
        target = threat_report.top_threat
        
        # --- Kinematic Leading ---
        # Lead the target based on its speed
        lead_y = 30
        enemy_card = self.card_db.get(target.name.replace("enemy_", ""))
        if enemy_card:
            speed = enemy_card.combat.speed_class if enemy_card.combat.speed_class else "medium"
            if speed == "very_fast":
                lead_y = 120
            elif speed == "fast":
                lead_y = 80
            elif speed == "slow":
                lead_y = 10

        # --- Phase 6: Kiting Logic ---
        heavy_melee_threats = {
            "pekka",
            "mega_knight",
            "giant_skeleton",
            "mini_pekka",
            "prince",
        }
        kite_units = {"skeletons", "ice_golem", "knight", "valkyrie"}

        enemy_name = target.name.replace("enemy_", "")
        if enemy_name in heavy_melee_threats and card_to_play in kite_units:
            # Drop in the center to pull the heavy unit away from the princess tower
            pull_x = 360
            if target.x < 360:
                pull_x += 50  # If enemy is on left, place slightly right to pull across center
            else:
                pull_x -= 50  # Pull across center from right
            # Drop high enough to pull them into the other lane if possible
            return int(pull_x), int(self.center_pull_y - 50)

        # --- Standard Defenses ---
        if card_to_play in self.spells:
            # Spells go directly on the target
            return int(target.x), int(target.y)

        if card_to_play in self.buildings:
            # Buildings go in the center to pull (kite) enemies
            pull_x = 360
            if target.x < 360:
                pull_x -= 30  # Pull slightly to the left
            else:
                pull_x += 30  # Pull slightly to the right
            return int(pull_x), int(self.center_pull_y)

        if card_to_play in self.ranged:
            # Ranged units should be placed safely away from the target
            safe_dist = 150
            if target.y < 800:
                # Target is high up, place ranged unit lower
                return int(target.x), int(target.y + safe_dist)
            else:
                # Target is dangerously close to our tower, place to the side
                side_offset = 100 if target.x > 360 else -100
                # Clamp to screen bounds
                safe_x = max(50, min(720 - 50, target.x + side_offset))
                return int(safe_x), int(target.y + 50)

        if card_to_play in self.swarms:
            # Swarms surround the target, drop exactly on centroid for max DPS
            return centroid_x, centroid_y

        # Default for Melee / Mini-tanks (Valkyrie, Knight, Mini PEKKA, etc.)
        # Drop slightly in front of the target to intercept using kinematic lead
        return int(target.x), int(target.y + lead_y)

    def _calculate_offensive_drop(self, card, report):
        """Determine where to drop a card when pushing."""
        # Determine which lane we are pushing
        push_x = 180 if report.hot_lane == "left" else 540

        if card in self.win_conditions:
            if card in ["goblin_barrel", "miner"]:
                # Drop directly on enemy princess tower (approximate coordinates)
                tower_y = 250
                return push_x, tower_y
            else:
                # Bridge spam
                return push_x, self.bridge_y

        if card in self.tanks:
            # Drop tanks in the back (behind king tower) to build a push
            back_y = 1100
            return push_x, back_y

        # Default offensive placement (support troops)
        # Drop behind the bridge
        return push_x, self.bridge_y + 100

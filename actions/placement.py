import math
from knowledge.card_database import CardDatabase

class PlacementEngine:
    def __init__(self):
        self.card_db = CardDatabase()
        # Base screen dimensions
        self.center_x = 360
        self.center_y = 640
        self.bridge_y = 700
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

    def _find_allied_tank(self, game_state):
        """Find the furthest-forward allied tank for support stacking."""
        best_tank = None
        best_y = 9999  # Lower Y = further toward enemy
        
        for troop in game_state.troops:
            if troop.team != "ally":
                continue
            card_key = troop.name.replace("ally_", "")
            if card_key in self.tanks and troop.y < best_y:
                best_y = troop.y
                best_tank = troop
        
        return best_tank

    def calculate_drop(self, card_to_play, threat_report, game_state):
        """
        Calculate optimal (x, y) coordinates to drop the card, with human-like jitter.
        """
        x, y = self._calculate_drop_internal(card_to_play, threat_report, game_state)
        
        if x is None or y is None:
            return None, None
            
        import random
        # Add human jitter so it never taps the exact same pixel
        # Standard deviation of 15 pixels
        jitter_x = random.randint(-15, 15)
        jitter_y = random.randint(-15, 15)
        
        final_x = max(20, min(700, x + jitter_x))
        final_y = max(100, min(1200, y + jitter_y))
        
        return final_x, final_y

    def _calculate_drop_internal(self, card_to_play, threat_report, game_state):
        """Internal logic for calculating exact coordinates."""
        if not card_to_play:
            return None, None

        # 1. Offensive Push (No immediate pressure)
        if not threat_report.pressure or not threat_report.top_threat:
            return self._calculate_offensive_drop(card_to_play, threat_report, game_state)

        # 2. Defensive Placement (Under pressure)
        target = threat_report.top_threat
        
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
            centroid_x, centroid_y = int(target.x), int(target.y)
        
        # --- Kinematic Leading ---
        # Lead the target based on its speed
        lead_y = 30
        lead_x = 0
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
            "skeleton_giant",
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

        # --- Split Push Detection ---
        left_enemies = [t for t in game_state.troops 
                       if t.team == "enemy" and t.x < self.center_x]
        right_enemies = [t for t in game_state.troops 
                        if t.team == "enemy" and t.x >= self.center_x]
        
        if left_enemies and right_enemies and card_to_play in self.buildings:
            # Under split push — place building in CENTER to pull from both lanes
            return 360, int(self.center_pull_y)

        # --- Standard Defenses ---
        if card_to_play in self.spells:
            # Spells should hit the cluster centroid, not just one troop
            if push_count > 1:
                return centroid_x + lead_x, centroid_y + lead_y
            return int(target.x) + lead_x, int(target.y) + lead_y

        if card_to_play in self.buildings:
            # Buildings go in the center to pull (kite) enemies
            pull_x = 360
            if target.x < 360:
                pull_x += 50  # Pull across center from left
            else:
                pull_x -= 50  # Pull across center from right
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
            # Splash units will destroy swarms instantly if dropped in front
            # We must SURROUND them by dropping exactly on their coordinate
            splash_units = {"wizard", "valkyrie", "executioner", "bomber", 
                            "dark_prince", "baby_dragon", "bowler", "firecracker", "sparky"}
            
            has_splash = False
            for troop in game_state.troops:
                if troop.team == "enemy" and troop.y > self.bridge_y - 100:
                    if (threat_report.hot_lane == "left" and troop.x < self.center_x) or \
                       (threat_report.hot_lane == "right" and troop.x > self.center_x):
                        if troop.name.replace("enemy_", "") in splash_units:
                            has_splash = True
                            break

            enemy_name = target.name.replace("enemy_", "")
            if enemy_name in splash_units or has_splash:
                # Drop exactly on top to surround
                return int(target.x), int(target.y)
                
            # For non-splash pushes, drop on centroid for max DPS
            return centroid_x, centroid_y

        # Default for Melee / Mini-tanks (Valkyrie, Knight, Mini PEKKA, etc.)
        # Drop slightly in front of the target to intercept using kinematic lead
        return int(target.x), int(target.y + lead_y)

    def _calculate_offensive_drop(self, card, report, game_state):
        """Determine where to drop a card when pushing."""
        # Determine which lane we are pushing (default to left if balanced)
        push_x = 180 if report.hot_lane != "right" else 540

        if card in self.win_conditions:
            if card in ["goblin_barrel", "miner"]:
                # Drop directly on enemy princess tower (approximate coordinates)
                tower_y = 250
                return push_x, tower_y
            else:
                # Bridge spam
                return push_x, self.bridge_y

        # If we have an allied tank pushing, stack support behind it
        allied_tank = self._find_allied_tank(game_state)
        if card in self.ranged and allied_tank and allied_tank.y < 900:  # Tank is in our half or crossing
            # Place support troop BEHIND the tank (higher Y = further back)
            return int(allied_tank.x), int(allied_tank.y + 120)

        if card in self.tanks:
            # Drop tanks in the back (behind king tower) to build a push
            back_y = 1050
            return push_x, back_y

        # Default offensive placement (support troops)
        # Drop behind the bridge
        return push_x, self.bridge_y + 100

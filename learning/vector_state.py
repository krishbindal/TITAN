import numpy as np
from knowledge.card_database import CardDatabase

class StateVectorizer:
    """
    Translates the TITAN GameState and UIState into a dense, fixed-size numerical tensor
    suitable for Deep Reinforcement Learning (DQN, PPO).
    """
    
    def __init__(self):
        self.card_db = CardDatabase()
        
        # Sort cards alphabetically to ensure deterministic indexing for one-hot encoding
        self.all_card_names = sorted(list(self.card_db.cards.keys()))
        self.num_cards = len(self.all_card_names)
        self.card_to_index = {name: i for i, name in enumerate(self.all_card_names)}
        
        # Grid settings for spatial representation
        # 2 lanes (Left/Right), 4 depth zones (0-3)
        self.lanes = 2
        self.depth_zones = 4

    def vectorize(self, game_state, ui_state, threat_report, elixir_tracker, memory, game_time):
        """
        Creates a flat numpy array representing the entire game board.
        """
        features = []
        
        # 1. Global Scalars (Normalized to 0.0 - 1.0)
        player_elixir = elixir_tracker.player_elixir / 10.0
        enemy_elixir = memory.enemy_elixir / 10.0 if memory else 0.5
        
        # Normalize game time (0 to 180 seconds typically, maxed at 300 for overtime)
        time_norm = min(game_time / 180.0, 1.0)
        
        # Tower HPs (Assuming max level 14 tower HP ~ 4000)
        max_hp = 4000.0
        left_hp = (ui_state.enemy_left_tower_hp / max_hp) if (ui_state and getattr(ui_state, 'enemy_left_tower_hp', None)) else 1.0
        right_hp = (ui_state.enemy_right_tower_hp / max_hp) if (ui_state and getattr(ui_state, 'enemy_right_tower_hp', None)) else 1.0
        
        features.extend([player_elixir, enemy_elixir, time_norm, left_hp, right_hp])
        
        # 2. Categorical Encodings
        pressure = 1.0 if threat_report.pressure else 0.0
        
        # Hot lane (One-hot: left, right, balanced)
        lane_left = 1.0 if threat_report.hot_lane == "left" else 0.0
        lane_right = 1.0 if threat_report.hot_lane == "right" else 0.0
        lane_balanced = 1.0 if threat_report.hot_lane == "balanced" else 0.0
        
        features.extend([pressure, lane_left, lane_right, lane_balanced])
        
        # 3. Card Multi-Hot Encodings
        # Player Hand
        hand_vector = np.zeros(self.num_cards)
        if game_state and game_state.hand:
            for card in game_state.hand:
                if card in self.card_to_index:
                    hand_vector[self.card_to_index[card]] = 1.0
        features.extend(hand_vector)
        
        # Enemy Deck Revealed
        enemy_deck_vector = np.zeros(self.num_cards)
        if memory and memory.deck:
            for card in memory.deck:
                if card in self.card_to_index:
                    enemy_deck_vector[self.card_to_index[card]] = 1.0
        features.extend(enemy_deck_vector)
        
        # 4. Spatial Arena Grid (2 lanes x 4 depth zones = 8 cells per team)
        # We will sum the elixir cost of troops in each cell
        ally_grid = np.zeros((self.lanes, self.depth_zones))
        enemy_grid = np.zeros((self.lanes, self.depth_zones))
        
        if game_state and game_state.troops:
            for troop in game_state.troops:
                # Determine lane (0 = Left, 1 = Right)
                lane_idx = 0 if troop.x < 360 else 1
                
                # Determine depth (0 = Enemy Deep, 1 = Enemy Shallow, 2 = Ally Shallow, 3 = Ally Deep)
                # Y goes from 0 (top, enemy side) to 1280 (bottom, ally side)
                y = max(0, min(troop.y, 1279))
                depth_idx = int(y // 320)  # 1280 / 4 = 320 pixels per zone
                
                # Get troop cost (or estimate as 4 if unknown)
                clean_name = troop.name.replace("ally_", "").replace("enemy_", "")
                troop_card = self.card_db.get(clean_name)
                cost = troop_card.cost if (troop_card and troop_card.cost) else 4.0
                
                if troop.team == "ally":
                    ally_grid[lane_idx, depth_idx] += cost
                else:
                    enemy_grid[lane_idx, depth_idx] += cost
                    
        # Flatten and normalize spatial grids (divide by max reasonable elixir per zone, e.g. 20)
        ally_flat = (ally_grid.flatten() / 20.0).clip(0.0, 1.0)
        enemy_flat = (enemy_grid.flatten() / 20.0).clip(0.0, 1.0)
        
        features.extend(ally_flat)
        features.extend(enemy_flat)
        
        return np.array(features, dtype=np.float32)

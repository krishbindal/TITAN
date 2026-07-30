"""
Elixir Tracker for TITAN.
Tracks both the player's elixir (from UI reading) and
estimates the opponent's elixir based on cards they play.
"""

from knowledge.card_database import CardDatabase


class ElixirTracker:
    """
    Tracks elixir economy for both players.

    Player elixir: Read directly from the UI.
    Opponent elixir: Estimated by tracking newly spawned enemy troops
    and subtracting their elixir cost from a running total.

    Elixir regenerates at 1 per 2.8 seconds (normal time)
    and 1 per 1.4 seconds (double elixir / overtime).
    """

    # Elixir generation rate: 1 elixir per N seconds
    NORMAL_RATE = 2.8
    DOUBLE_RATE = 1.4

    MAX_ELIXIR = 10

    def __init__(self):
        self.card_db = CardDatabase()

        # Player elixir (from UI)
        self.player_elixir = 5.0

        # Opponent elixir (estimated)
        self.opponent_elixir = 5.0

        # Track which enemy track IDs we already counted
        self._known_enemy_ids = set()
        
        # Track when we last billed a card type to prevent multi-counting swarms
        self._last_card_play_times = {}

        # Game clock tracking for elixir regen
        self._last_update_time = 0.0
        self._double_elixir = False

    def set_double_elixir(self, enabled: bool):
        """Switch to double elixir rate (called at 1:00 remaining)."""
        self._double_elixir = enabled

    def update(self, game_state, ui_state, game_time: float):
        """
        Update elixir tracking each frame.

        Args:
            game_state: Current GameState with troops
            ui_state: UIState with player_elixir
            game_time: Current game time in seconds
        """
        # --- Player Elixir ---
        # Read from UI (ground truth) but also maintain time-based estimate as a floor.
        # This prevents OCR misreads (e.g., reading 0 when we have 10) from breaking strategy.
        
        # Time-based estimate (always computed)
        time_estimate = self.player_elixir
        if self._last_update_time > 0:
            elapsed = game_time - self._last_update_time
            rate = self.DOUBLE_RATE if self._double_elixir else self.NORMAL_RATE
            regen = elapsed / rate
            time_estimate = min(self.MAX_ELIXIR, self.player_elixir + regen)
        
        if ui_state and hasattr(ui_state, "player_elixir") and ui_state.player_elixir is not None:
            ocr_val = ui_state.player_elixir
            
            # Trust OCR if it drops (indicates a play we missed) or if it's within bounds
            if ocr_val < self.player_elixir - 0.5:
                # Big drop means card played
                self.player_elixir = ocr_val
            elif abs(ocr_val - time_estimate) <= 2.0:
                # Plausible read, trust it and snap
                self.player_elixir = ocr_val
            else:
                # OCR read is wildly different without a drop (e.g. read 10 when we have 2)
                # Fall back to time estimate
                self.player_elixir = time_estimate
        else:
            # OCR failed — use time-based estimate
            self.player_elixir = time_estimate

        # --- Opponent Elixir ---
        # Step 1: Regenerate elixir over time
        if self._last_update_time > 0:
            elapsed = game_time - self._last_update_time
            rate = self.DOUBLE_RATE if self._double_elixir else self.NORMAL_RATE
            regen = elapsed / rate
            self.opponent_elixir = min(self.MAX_ELIXIR, self.opponent_elixir + regen)

        # Step 2: Subtract elixir for newly spawned enemy troops
        for troop in game_state.troops:
            if troop.team != "enemy":
                continue

            if troop.track_id in self._known_enemy_ids:
                continue

            self._known_enemy_ids.add(troop.track_id)
            
            # Swarm cooldown: if we just billed this card type recently, ignore the clone
            card_key = self.card_db.normalize(troop.name)
            last_played = self._last_card_play_times.get(card_key, -10.0)
            if game_time - last_played < 2.0:
                continue
                
            self._last_card_play_times[card_key] = game_time

            card = self.card_db.get(card_key)
            if card and card.cost:
                self.opponent_elixir = max(0.0, self.opponent_elixir - card.cost)

        self._last_update_time = game_time

    def get_elixir_advantage(self):
        """
        Returns the elixir advantage (positive = we're ahead).
        """
        return self.player_elixir - self.opponent_elixir

    def deduct_card_play(self, card_name):
        """
        Deduct elixir when we play a card (called from play_live.py).
        """
        if card_name.startswith("unknown_"):
            cost = 3.0
        else:
            card = self.card_db.get(card_name)
            cost = card.cost if card and card.cost else 3.0
        self.player_elixir = max(0.0, self.player_elixir - cost)

    def __str__(self):
        advantage = self.get_elixir_advantage()
        sign = "+" if advantage >= 0 else ""
        return (
            f"Elixir | "
            f"Player: {self.player_elixir:.1f} | "
            f"Opponent: {self.opponent_elixir:.1f} | "
            f"Advantage: {sign}{advantage:.1f}"
        )

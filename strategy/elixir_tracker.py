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
            # Use the HIGHER of OCR and time-estimate to avoid underestimation
            # (OCR can misread 10 as 0, but time-based can't overshoot past 10)
            self.player_elixir = max(ocr_val, time_estimate)
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

            # New enemy troop detected!
            self._known_enemy_ids.add(troop.track_id)

            # Look up its elixir cost
            card_key = troop.name.replace("enemy_", "")
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

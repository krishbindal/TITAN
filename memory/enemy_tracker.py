"""
Enemy Tracker — TITAN's Memory.
Tracks the enemy's deck and cycle by observing what they play on the battlefield.
"""

from collections import deque
from knowledge.card_database import CardDatabase

class EnemyTracker:
    def __init__(self):
        self.card_db = CardDatabase()
        
        # The enemy's discovered deck (up to 8 unique cards)
        self.deck = set()

        # The sequence of cards the enemy has played recently
        # Clash Royale decks have 8 cards. Once a card is played,
        # 4 other cards must be played before it's back in their hand.
        self.play_history = []

        # We track which specific YOLO detection IDs we've already counted
        # so we don't count the same spawned troop twice.
        self._counted_track_ids = set()

    def update(self, game_state, game_time=0.0):
        """Update memory based on the current battlefield."""
        
        for troop in game_state.troops:
            if troop.team != "enemy":
                continue

            if troop.track_id in self._counted_track_ids:
                continue

            # New enemy card detected!
            self._counted_track_ids.add(troop.track_id)
            card_key = troop.name.replace("enemy_", "")

            # Add to discovered deck
            if len(self.deck) < 8:
                self.deck.add(card_key)

            # Add to play history
            self.play_history.append(card_key)

    def is_in_cycle(self, card_key):
        """
        Check if the enemy likely has this card in their current hand.
        If they played it within the last 4 cards, it's NOT in their hand.
        """
        if card_key not in self.deck:
            return False  # We haven't seen it yet

        # Get the last 4 cards played
        last_4 = (
            self.play_history[-4:] if len(self.play_history) >= 4 else self.play_history
        )

        if card_key in last_4:
            return False  # They played it recently, it's not back in their hand yet

        return True  # It's been >= 4 cards, so it's in their hand

    def has_win_condition_in_cycle(self):
        """
        Check if the enemy likely has a win condition ready to play.
        """
        win_conditions = {
            "hog_rider", "giant", "golem", "balloon", "miner", 
            "goblin_barrel", "royal_giant", "wall_breakers", "battle_ram",
            "ram_rider", "goblin_drill", "skeleton_barrel", "graveyard",
            "lava_hound", "xbow", "mortar"
        }
        
        for card in self.deck:
            if card in win_conditions and self.is_in_cycle(card):
                return True
        return False


    def clear(self):
        """Reset memory for a new match."""
        self.deck.clear()
        self.play_history.clear()
        self._counted_track_ids.clear()

    def __str__(self):
        deck_str = ", ".join(self.deck) if self.deck else "Unknown"
        history_str = (
            " -> ".join(self.play_history[-4:]) if self.play_history else "None"
        )
        return (
            f"Enemy Deck [{len(self.deck)}/8]: {deck_str}\n"
            f"Recent Plays: {history_str}"
        )

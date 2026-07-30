import json
import os
import random
import hashlib

class DeckOptimizer:
    def __init__(self, data_file="models/deck_stats.json"):
        self.data_file = data_file
        self.deck_stats = {} # Map of deck_hash -> {"deck": [], "wins": 0, "losses": 0, "win_rate": 0.0}
        self.load()

    def _hash_deck(self, deck):
        # Sort the deck so order doesn't matter, then hash it
        sorted_deck = sorted(deck)
        deck_str = ",".join(sorted_deck)
        return hashlib.md5(deck_str.encode('utf-8')).hexdigest()

    def load(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.deck_stats = json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.deck_stats, f, indent=4)

    def record_match(self, deck, won):
        if not deck or len(deck) < 8:
            return

        deck_hash = self._hash_deck(deck)
        if deck_hash not in self.deck_stats:
            self.deck_stats[deck_hash] = {
                "deck": sorted(deck),
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_games": 0
            }

        if won:
            self.deck_stats[deck_hash]["wins"] += 1
        else:
            self.deck_stats[deck_hash]["losses"] += 1

        total = self.deck_stats[deck_hash]["wins"] + self.deck_stats[deck_hash]["losses"]
        self.deck_stats[deck_hash]["total_games"] = total
        self.deck_stats[deck_hash]["win_rate"] = self.deck_stats[deck_hash]["wins"] / total
        self.save()

    def suggest_deck(self, available_cards, core_deck, epsilon=0.2):
        """
        Suggests a deck to play.
        - With probability epsilon, mutates the core_deck by swapping 1-2 cards to explore.
        - Otherwise, exploits by picking the deck with the highest win_rate from history,
          or falls back to core_deck if no history exists.
        """
        # If we have no history or exploring, mutate the core deck
        if not self.deck_stats or random.random() < epsilon:
            return self._mutate_deck(core_deck, available_cards)

        # Exploit: Pick best deck that we have the cards for
        best_deck = None
        best_win_rate = -1.0
        
        for d_hash, stats in self.deck_stats.items():
            # Check if we still have all these cards available
            deck = stats["deck"]
            if all(card in available_cards for card in deck):
                # Prefer decks with more games if win rate is similar (UCB logic simplified)
                score = stats["win_rate"] + (0.1 if stats["total_games"] > 5 else 0)
                if score > best_win_rate:
                    best_win_rate = score
                    best_deck = deck

        if best_deck:
            return best_deck
            
        return self._mutate_deck(core_deck, available_cards)

    def _mutate_deck(self, core_deck, available_cards):
        """Swaps 1 or 2 cards randomly from the core deck with available cards."""
        if not available_cards or len(available_cards) <= 8:
            return core_deck
            
        new_deck = list(core_deck)
        num_swaps = random.choice([1, 2])
        
        pool = [c for c in available_cards if c not in new_deck]
        
        for _ in range(num_swaps):
            if not pool:
                break
            idx_to_remove = random.randint(0, 7)
            card_to_add = random.choice(pool)
            pool.remove(card_to_add)
            
            new_deck[idx_to_remove] = card_to_add
            
        return new_deck

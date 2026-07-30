"""
Auto-Updater for Clash Royale Card Database.
Pulls latest stats (balances/nerfs/buffs) and updates knowledge/cards.json.

Since there is no official API for exact stats, this uses a placeholder/mock
system that can be hooked up to RoyaleAPI or a web scraper later.
"""

import json
import os
from datetime import datetime

# Path to the cards database
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "knowledge",
    "cards.json",
)

# Mock update data (example of balance changes)
MOCK_UPDATES = {
    "hog_rider": {"hit_speed": 1.7},  # Nerfed attack speed
    "knight": {"hp": 1500},  # Buffed health
    "fire_cracker": {"damage": 270},  # Buffed damage
}


def update_cards():
    print(f"Loading database from {DB_PATH}")

    try:
        with open(DB_PATH, "r") as f:
            cards = json.load(f)
    except FileNotFoundError:
        print("Database not found! Creating new.")
        cards = {}

    updates_applied = 0

    print("\nChecking for balance changes...")
    for card_key, changes in MOCK_UPDATES.items():
        if card_key in cards:
            print(f"Updating {card_key}:")
            for stat, new_val in changes.items():
                old_val = cards[card_key].get(stat, "N/A")
                if old_val != new_val:
                    print(f"  - {stat}: {old_val} -> {new_val}")
                    cards[card_key][stat] = new_val
                    updates_applied += 1
        else:
            print(f"Card {card_key} not found in database. Skipping.")

    if updates_applied > 0:
        cards["_metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "version": "season_52_balance",
        }

        with open(DB_PATH, "w") as f:
            json.dump(cards, f, indent=4)

        print(f"\nSuccessfully applied {updates_applied} updates to the database.")
    else:
        print("\nNo balance changes needed. Database is up to date.")


if __name__ == "__main__":
    update_cards()

"""
Counter Matrix — teaches TITAN which cards beat which.
Maps enemy card keys to a ranked list of counter cards.
"""

# Each key is an enemy card. The value is a list of counters
# ordered from best to worst.
# Format: { "enemy_card_key": ["counter1", "counter2", ...] }

COUNTER_MATRIX = {
    # --- Tanks ---
    "pekka": ["skeleton_army", "inferno_tower", "inferno_dragon", "minion_horde"],
    "golem": ["inferno_tower", "inferno_dragon", "skeleton_army", "pekka"],
    "giant": ["inferno_tower", "mini_pekka", "skeleton_army", "pekka"],
    "giant_skeleton": ["skeleton_army", "tombstone", "inferno_tower"],
    "lava_hound": ["inferno_tower", "inferno_dragon", "musketeer", "minion_horde"],
    "mega_knight": ["pekka", "inferno_tower", "inferno_dragon", "knight"],
    "royal_giant": ["inferno_tower", "mini_pekka", "pekka", "skeleton_army"],
    # --- Win Conditions ---
    "hog_rider": ["cannon", "tornado", "skeleton_army", "mini_pekka"],
    "ram_rider": ["tombstone", "skeleton_army", "mini_pekka"],
    "balloon": ["musketeer", "minions", "wizard", "inferno_dragon"],
    "graveyard": ["valkyrie", "poison", "archers"],
    "goblin_barrel": ["log", "barbarian_barrel", "valkyrie"],
    "miner": ["knight", "valkyrie", "skeletons"],
    "wall_breakers": ["log", "skeletons", "zap"],
    # --- Swarms ---
    "skeleton_army": ["log", "zap", "valkyrie", "arrows", "fireball"],
    "minion_horde": ["arrows", "fireball", "wizard", "zap"],
    "goblin_gang": ["log", "valkyrie", "arrows"],
    "bats": ["zap", "arrows", "wizard"],
    "skeletons": ["zap", "log"],
    # --- Support ---
    "wizard": ["fireball", "lightning", "rocket"],
    "witch": ["fireball", "lightning", "valkyrie", "knight"],
    "musketeer": ["fireball", "knight", "mini_pekka"],
    "electro_wizard": ["fireball", "knight", "mini_pekka"],
    "baby_dragon": ["musketeer", "inferno_dragon", "minions"],
    "executioner": ["lightning", "rocket", "pekka"],
    "sparky": ["zap", "electro_wizard", "rocket", "skeleton_army"],
    # --- Spells (can't be "countered" but we can predict reactions) ---
    "fireball": [],
    "zap": [],
    "log": [],
    "arrows": [],
    "lightning": [],
    "rocket": [],
    "poison": [],
    # --- Buildings ---
    "inferno_tower": ["lightning", "zap", "electro_wizard", "minion_horde"],
    "cannon": ["fireball", "miner", "hog_rider"],
    "tesla": ["fireball", "earthquake", "miner"],
    "bomb_tower": ["fireball", "lightning", "miner"],
    "tombstone": ["valkyrie", "poison", "fireball"],
    "furnace": ["fireball", "poison", "miner"],
    "goblin_hut": ["fireball", "poison", "miner"],
    "elixir_collector": ["fireball", "miner", "rocket", "earthquake"],
    # --- Mini Tanks ---
    "knight": ["skeleton_army", "minions", "valkyrie"],
    "valkyrie": ["mini_pekka", "pekka", "inferno_tower", "skeleton_army"],
    "mini_pekka": ["skeleton_army", "guards", "knight"],
    "dark_prince": ["valkyrie", "pekka", "skeleton_army"],
    "prince": ["skeleton_army", "guards", "tombstone"],
    "bandit": ["knight", "mini_pekka", "skeleton_army"],
    "lumberjack": ["skeleton_army", "knight", "mini_pekka"],
    "fire_cracker": ["log", "arrows", "fireball", "zap"],
    "fire_ball": ["zap", "log"],
}


def get_counters(enemy_card_key: str) -> list:
    """
    Get the list of counter cards for a given enemy card.
    Returns an empty list if the card is unknown.
    """
    return COUNTER_MATRIX.get(enemy_card_key, [])


def best_counter(enemy_card_key: str, available_cards: list) -> str | None:
    """
    Given an enemy card and a list of cards available in the player's hand,
    return the best counter. Returns None if no counter is available.

    Args:
        enemy_card_key: The enemy card key (e.g., "hog_rider")
        available_cards: List of card keys in the player's hand

    Returns:
        The best counter card key, or None
    """
    counters = get_counters(enemy_card_key)
    for counter in counters:
        if counter in available_cards:
            return counter
    return None

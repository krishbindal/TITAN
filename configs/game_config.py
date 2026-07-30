"""
TITAN Game Configuration.
Set these values to match your current Clash Royale profile.
The strategy engine uses these to scale stats and adjust playstyle.
"""

# === Player Profile ===
PLAYER_LEVEL = 14
AVERAGE_CARD_LEVEL = 14

# === Arena / League ===
# Common values: "arena_15", "challenger_1", "challenger_2",
#                "challenger_3", "master_1", "champion", "ultimate_champion"
CURRENT_ARENA = "challenger_2"

# === Game Mode ===
# The active AI mode: 'standard', 'sudden_death', or 'rl'
GAME_MODE = "rl"

# === Level Inference ===
ARENA_LEVEL_MAP = {
    "arena_1": 1,
    "arena_2": 2,
    "arena_3": 3,
    "arena_4": 4,
    "arena_5": 5,
    "arena_6": 6,
    "arena_7": 7,
    "arena_8": 8,
    "arena_9": 9,
    "arena_10": 10,
    "arena_11": 11,
    "arena_12": 11,
    "arena_13": 12,
    "arena_14": 12,
    "arena_15": 13,
    "challenger_1": 13,
    "challenger_2": 14,
    "challenger_3": 14,
    "master_1": 14,
    "master_2": 15,
    "master_3": 15,
    "champion": 15,
    "grand_champion": 15,
    "royal_champion": 15,
    "ultimate_champion": 15,
}


def get_expected_enemy_level():
    """Return the expected enemy card level based on current arena."""
    return ARENA_LEVEL_MAP.get(CURRENT_ARENA, 11)

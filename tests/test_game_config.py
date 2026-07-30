"""
Regression tests for game configuration.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.game_config import (
    GAME_MODE,
    CURRENT_ARENA,
    ARENA_LEVEL_MAP,
    get_expected_enemy_level,
)


def test_game_mode_valid():
    """Game mode should be a recognized value."""
    valid_modes = {"standard", "sudden_death", "triple_elixir", "2v2"}
    assert GAME_MODE in valid_modes


def test_arena_in_map():
    """Current arena should exist in the level map."""
    assert CURRENT_ARENA in ARENA_LEVEL_MAP


def test_expected_level_range():
    """Expected enemy level should be between 1 and 15."""
    level = get_expected_enemy_level()
    assert 1 <= level <= 15


def test_level_map_completeness():
    """Every arena in the map should have a valid level."""
    for arena, level in ARENA_LEVEL_MAP.items():
        assert 1 <= level <= 15, f"{arena} has invalid level {level}"

"""
Unit tests for the Strategy engine and pluggable modes.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_builder.game_state import GameState
from state_builder.troop import Troop
from strategy.actions import Action
from strategy.modes import standard, sudden_death
from strategy.threat_assessment import ThreatAssessment
from strategy.elixir_tracker import ElixirTracker
from memory.enemy_tracker import EnemyTracker
from actions.placement import PlacementEngine


def _make_state(troops=None, hand=None):
    """Helper to build a GameState for testing."""
    state = GameState()
    if troops:
        for t in troops:
            state.troops.append(t)
    if hand:
        state.hand = hand
    return state


def test_standard_wait_empty_field():
    """Standard mode should WAIT when no troops and low elixir."""
    state = _make_state(hand=["knight", "fireball"])
    threat = ThreatAssessment()
    elixir = ElixirTracker()
    memory = EnemyTracker()
    placement = PlacementEngine()
    elixir.player_elixir = 5  # Not maxed

    action = standard.decide(state, threat, elixir, memory, placement)
    assert action.action == Action.WAIT


def test_standard_push_at_max_elixir():
    """Standard mode should push when at max elixir and no troops."""
    state = _make_state(hand=["hog_rider", "fireball"])
    threat = ThreatAssessment()
    elixir = ElixirTracker()
    memory = EnemyTracker()
    placement = PlacementEngine()
    elixir.player_elixir = 10

    action = standard.decide(state, threat, elixir, memory, placement)
    assert action.action == Action.PLAY_CARD
    assert action.card_to_play == "hog_rider"  # Win con prioritized


def test_standard_defend_under_pressure():
    """Standard mode should defend when enemy is in the danger zone."""
    enemy = Troop(1, "enemy_hog_rider", 360, 800, "enemy")
    state = _make_state(troops=[enemy], hand=["cannon", "fireball"])
    threat = ThreatAssessment()
    elixir = ElixirTracker()
    memory = EnemyTracker()
    placement = PlacementEngine()
    elixir.player_elixir = 5

    action = standard.decide(state, threat, elixir, memory, placement)
    assert action.action == Action.PLAY_CARD
    assert action.card_to_play == "cannon"  # Counter from matrix


def test_sudden_death_aggressive():
    """Sudden death should play cards aggressively even without threats."""
    state = _make_state(hand=["hog_rider", "fireball"])
    threat = ThreatAssessment()
    elixir = ElixirTracker()
    memory = EnemyTracker()
    placement = PlacementEngine()
    elixir.player_elixir = 5

    action = sudden_death.decide(state, threat, elixir, memory, placement)
    assert action.action == Action.PLAY_CARD
    assert action.card_to_play == "hog_rider"  # Win con prioritized


def test_sudden_death_still_defends():
    """Sudden death should still counter heavy pressure."""
    enemy = Troop(1, "enemy_pekka", 360, 800, "enemy")
    state = _make_state(troops=[enemy], hand=["skeleton_army", "fireball"])
    threat = ThreatAssessment()
    elixir = ElixirTracker()
    memory = EnemyTracker()
    placement = PlacementEngine()
    elixir.player_elixir = 5

    action = sudden_death.decide(state, threat, elixir, memory, placement)
    assert action.action == Action.PLAY_CARD
    assert action.card_to_play == "skeleton_army"  # Counter PEKKA

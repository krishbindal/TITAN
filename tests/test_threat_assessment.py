"""
Unit tests for ThreatAssessment math.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_builder.game_state import GameState
from state_builder.troop import Troop
from strategy.threat_assessment import ThreatAssessment


def _make_state(troops):
    state = GameState()
    for t in troops:
        state.troops.append(t)
    return state


def test_empty_field_no_threat():
    """Empty field should produce zero threat."""
    state = _make_state([])
    ta = ThreatAssessment()
    report = ta.assess(state)
    assert report.total_dps == 0
    assert report.enemy_count == 0
    assert report.pressure is False


def test_ally_ignored():
    """Ally troops should not count as threats."""
    ally = Troop(1, "ally_knight", 300, 500, "ally")
    state = _make_state([ally])
    ta = ThreatAssessment()
    report = ta.assess(state)
    assert report.enemy_count == 0


def test_enemy_in_danger_zone():
    """Enemy past Y=700 should trigger pressure."""
    enemy = Troop(1, "enemy_hog_rider", 300, 800, "enemy")
    state = _make_state([enemy])
    ta = ThreatAssessment()
    report = ta.assess(state)
    assert report.pressure is True
    assert report.enemy_count == 1


def test_lane_assignment():
    """Troops left of center go to left_dps, right to right_dps."""
    left_enemy = Troop(1, "enemy_knight", 100, 500, "enemy")
    right_enemy = Troop(2, "enemy_knight", 500, 500, "enemy")
    state = _make_state([left_enemy, right_enemy])
    ta = ThreatAssessment()
    report = ta.assess(state)
    assert report.left_dps > 0
    assert report.right_dps > 0


def test_hot_lane_detection():
    """A single enemy on one side should make that the hot lane."""
    enemy = Troop(1, "enemy_pekka", 100, 500, "enemy")
    state = _make_state([enemy])
    ta = ThreatAssessment()
    report = ta.assess(state)
    assert report.hot_lane == "left"

"""
Unit tests for the Track confirmation system.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tracker.detection import Detection
from tracker.tracker import Tracker


def test_new_track_is_tentative():
    """A brand-new track should NOT be confirmed after 1 frame."""
    tracker = Tracker()
    det = Detection("hog_rider", 400, 300, 60, 80, 0.98)
    tracker.update([det], 0)
    confirmed = tracker.get_confirmed_tracks()
    assert len(confirmed) == 0


def test_track_confirms_after_n_frames():
    """A track should be confirmed after CONFIRM_FRAMES consecutive hits."""
    tracker = Tracker()

    for i in range(tracker.confirm_frames + 1):
        det = Detection("hog_rider", 400 + i, 300, 60, 80, 0.98)
        tracker.update([det], i)

    confirmed = tracker.get_confirmed_tracks()
    assert len(confirmed) == 1
    assert confirmed[0].name == "hog_rider"


def test_tentative_track_removed_quickly():
    """A tentative track that disappears should be removed in 2 frames."""
    tracker = Tracker()
    det = Detection("goblin", 200, 200, 30, 30, 0.60)
    tracker.update([det], 0)

    # Miss it for 3 frames
    for i in range(1, 4):
        tracker.update([], i)

    assert len(tracker.tracks) == 0


def test_confirmed_track_survives_misses():
    """A confirmed track should survive up to max_missed_frames misses."""
    tracker = Tracker()

    # Confirm it first
    for i in range(tracker.confirm_frames + 1):
        det = Detection("knight", 300, 400, 50, 50, 0.95)
        tracker.update([det], i)

    confirmed = tracker.get_confirmed_tracks()
    assert len(confirmed) == 1

    # Miss a few frames (but less than max_missed_frames)
    for i in range(tracker.confirm_frames + 1, tracker.confirm_frames + 5):
        tracker.update([], i)

    confirmed = tracker.get_confirmed_tracks()
    assert len(confirmed) == 1  # Should still be alive

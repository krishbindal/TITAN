"""
Integration tests for the TITAN AI Pipeline.
"""

import sys
import os
import numpy as np
from unittest.mock import MagicMock

# Mock ultralytics before importing pipeline
sys.modules["ultralytics"] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.pipeline import Pipeline
from vision.screen_classifier import ScreenState


class MockDetector:
    def __init__(self):
        self.dummy_detections = []

    def detect(self, frame):
        return self.dummy_detections


def test_pipeline_non_gameplay_frame():
    """Pipeline should skip full processing for non-gameplay screens."""
    pipeline = Pipeline(model_path="dummy")
    # Inject mock detector so it doesn't try to load YOLO
    pipeline.detector = MockDetector()

    # Create a dummy solid blue frame (victory screen)
    frame = np.zeros((1280, 720, 3), dtype=np.uint8)
    frame[200:450, 150:570] = [120, 200, 200]  # Blue in BGR

    # We can fake the HSV conversion outcome by mocking classify,
    # but the logic actually looks at the frame. Let's just mock the classifier
    # to guarantee a fast test.
    pipeline.screen_classifier.classify = lambda f: ScreenState.VICTORY

    game_state, action, screen_state = pipeline.process_frame(frame)

    assert screen_state == ScreenState.VICTORY
    assert game_state is None
    assert action is None


def test_pipeline_gameplay_frame():
    """Pipeline should process gameplay frames fully."""
    pipeline = Pipeline(model_path="dummy")
    pipeline.detector = MockDetector()

    # Force gameplay state
    pipeline.screen_classifier.classify = lambda f: ScreenState.GAMEPLAY

    # Empty frame
    frame = np.zeros((1280, 720, 3), dtype=np.uint8)

    game_state, action, screen_state = pipeline.process_frame(frame)

    assert screen_state == ScreenState.GAMEPLAY
    assert game_state is not None
    # Action might be WAIT or DO_NOTHING depending on elixir tracker state
    assert action is not None

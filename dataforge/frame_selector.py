import cv2

from dataforge.duplicate_filter import DuplicateFilter
from vision.screen_classifier import ScreenClassifier
from configs.settings import (
    FRAME_EXTRACT_INTERVAL,
    DUPLICATE_THRESHOLD,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class FrameSelector:

    def __init__(self, interval=None, duplicate_threshold=None):

        self.interval = interval or FRAME_EXTRACT_INTERVAL

        self.duplicate_filter = DuplicateFilter(
            threshold=duplicate_threshold or DUPLICATE_THRESHOLD
        )

        self.screen_classifier = ScreenClassifier()

        self.target_width = SCREEN_WIDTH
        self.target_height = SCREEN_HEIGHT

    def should_select(self, frame, frame_number):
        """Decide if this frame should be extracted."""

        # Only check every Nth frame
        if frame_number % self.interval != 0:
            return False

        # Skip non-gameplay frames (menus, loading, victory)
        if not self.screen_classifier.is_gameplay(frame):
            return False

        # Skip near-duplicate frames
        if not self.duplicate_filter.should_save(frame):
            return False

        return True

    def normalize(self, frame):
        """Resize frame to standard resolution."""

        h, w = frame.shape[:2]

        if w != self.target_width or h != self.target_height:
            frame = cv2.resize(frame, (self.target_width, self.target_height))

        return frame

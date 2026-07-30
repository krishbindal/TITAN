from vision.detector import Detector
from vision.screen_classifier import ScreenClassifier, ScreenState
from vision.region_filter import RegionFilter
from tracker.tracker import Tracker
from world.event_detector import EventDetector
from vision.visualizer import Visualizer

from actions.action_detector import ActionDetector


class TitanEngine:

    def __init__(self, model_path):

        self.screen_classifier = ScreenClassifier()

        self.detector = Detector(model_path)

        self.region_filter = RegionFilter()

        self.tracker = Tracker()

        self.event_detector = EventDetector()

        self.action_detector = ActionDetector()

        self.visualizer = Visualizer()

    def process_frame(self, frame, frame_number, time):

        # Step 1: Classify screen state
        screen_state = self.screen_classifier.classify(frame)

        if screen_state != ScreenState.GAMEPLAY:
            return frame, [], [], screen_state

        # Step 2: Detect objects
        detections = self.detector.detect(frame)

        # Step 3: Filter by screen region
        detections = self.region_filter.filter(detections)

        # Step 4: Track objects
        self.tracker.update(detections, frame_number)

        # Step 5: Get only confirmed tracks
        confirmed = self.tracker.get_confirmed_tracks()

        # Step 6: Detect actions on confirmed tracks
        for track in confirmed:

            self.action_detector.detect(track)

        # Step 7: Detect events from confirmed tracks
        events = self.event_detector.update(confirmed, time)

        # Step 8: Visualize all detections (for debug)
        output = self.visualizer.draw(frame, detections)

        return output, confirmed, events, screen_state



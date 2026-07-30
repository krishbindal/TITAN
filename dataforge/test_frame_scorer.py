from tracker.detection import Detection
from dataforge.frame_scorer import FrameScorer

detections = [
    Detection("Knight", 100, 100, 40, 40, 0.96, "blue"),
    Detection("Musketeer", 200, 250, 40, 40, 0.94, "blue"),
    Detection("Tower", 500, 150, 60, 120, 0.99, "red"),
]

scorer = FrameScorer()

print("Frame Score:", scorer.score(detections))

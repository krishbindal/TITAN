from tracker.detection import Detection
from dataforge.active_learning import ActiveLearning

detections = [
    Detection("Knight", 100, 100, 40, 40, 0.95, "blue"),
    Detection("Wizard", 200, 200, 40, 40, 0.41, "red"),
]

engine = ActiveLearning()

print(engine.needs_review(detections))

from tracker.detection import Detection
from tracker.tracker import Tracker

tracker = Tracker()

frames = [
    Detection("hog_rider", 400, 300, 60, 80, 0.98),
    Detection("hog_rider", 410, 308, 60, 80, 0.97),
    Detection("hog_rider", 420, 317, 60, 80, 0.99),
]

for i, detection in enumerate(frames):
    tracker.update([detection], i)

for track in tracker.tracks:
    print(track)

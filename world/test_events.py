from tracker.detection import Detection
from tracker.track import Track

from world.event_detector import EventDetector

detector = EventDetector()


tracks = []

detection = Detection(
    "Knight",
    200,
    400,
    50,
    50,
    0.95,
)

track = Track(1, detection, 0)

tracks.append(track)

events = detector.update(tracks, 0.5)

for event in events:

    print(event)


events = detector.update([], 3.0)

for event in events:

    print(event)

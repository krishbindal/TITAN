import os
import cv2
from vision.detector import Detector
from configs.settings import GAMEPLAY_ZONE_BOTTOM, CARD_ZONE_TOP

pipeline = Detector("models/best.pt")

video_dir = "C:/Users/krish/Music/clash royale"
videos = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
video_path = os.path.join(video_dir, videos[0])

print(f"Checking for cards in {video_path}")
print(
    f"Settings: GAMEPLAY_ZONE_BOTTOM={GAMEPLAY_ZONE_BOTTOM}, CARD_ZONE_TOP={CARD_ZONE_TOP}"
)

cap = cv2.VideoCapture(video_path)

cards_found = False
for i in range(3000):  # Check up to 100 seconds
    ret, frame = cap.read()
    if not ret:
        break

    if i % 30 != 0:
        continue  # Check 1 frame per second

    frame = cv2.resize(frame, (720, 1280))
    detections = pipeline.detect(frame)

    cards = [d for d in detections if d.name.startswith("card_")]
    if cards:
        print(f"Frame {i}: Found {len(cards)} cards")
        for c in cards:
            cx, cy = c.center()
            print(f"  {c.name} at Y={cy} (x={c.x}, y={c.y}, w={c.width}, h={c.height})")
        cards_found = True
        break

if not cards_found:
    print("NO CARDS FOUND IN THE FIRST 100 SECONDS OF VIDEO.")

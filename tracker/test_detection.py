from tracker.detection import Detection

hog = Detection(
    name="hog_rider", x=400, y=220, width=60, height=80, confidence=0.97, team="enemy"
)

print(hog)

print(hog.center())

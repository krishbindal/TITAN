import cv2

cap = cv2.VideoCapture("replays/game1.mp4")

print("Opened:", cap.isOpened())
print("FPS:", cap.get(cv2.CAP_PROP_FPS))
print("Frames:", int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))

success, frame = cap.read()
print("First frame read:", success)

cap.release()

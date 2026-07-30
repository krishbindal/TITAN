import cv2

from dataforge.duplicate_filter import DuplicateFilter

cap = cv2.VideoCapture("replays/game1.mp4")

filter = DuplicateFilter()

saved = 0
frame_no = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    if filter.should_save(frame):
        saved += 1

    frame_no += 1

cap.release()

print("Total Frames :", frame_no)
print("Useful Frames:", saved)

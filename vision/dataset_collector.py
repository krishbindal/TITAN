import mss
import cv2
import numpy as np
import os
import time

SAVE_DIR = "data/raw"

os.makedirs(SAVE_DIR, exist_ok=True)

with mss.mss() as sct:

    monitor = sct.monitors[1]

    count = 0

    while True:

        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)

        cv2.imshow("Titan Vision", frame)

        key = cv2.waitKey(1)

        if key == ord("s"):
            filename = os.path.join(SAVE_DIR, f"frame_{count:05d}.png")
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
            count += 1

        elif key == ord("q"):
            break

cv2.destroyAllWindows()

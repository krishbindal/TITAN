import mss
import cv2
import numpy as np

with mss.mss() as sct:

    monitor = sct.monitors[1]

    while True:

        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)

        print(frame.shape)

        cv2.imshow("Titan Vision", frame)

        if cv2.waitKey(1) == ord("q"):
            break

cv2.destroyAllWindows()

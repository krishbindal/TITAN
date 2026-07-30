import mss
import cv2
import numpy as np

with mss.mss() as sct:

    monitor = sct.monitors[1]

    screenshot = sct.grab(monitor)

    img = np.array(screenshot)

    cv2.imwrite("data/raw/screenshot.png", img)

    print("Screenshot saved successfully!")

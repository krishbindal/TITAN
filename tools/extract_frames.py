import os
import cv2


class FrameExtractor:
    def __init__(self, video_path, output_folder, interval=30):
        """
        interval = save every Nth frame
        """
        self.video_path = video_path
        self.output_folder = output_folder
        self.interval = interval

        os.makedirs(output_folder, exist_ok=True)

    def extract(self):
        cap = cv2.VideoCapture(self.video_path)

        frame_number = 0
        saved = 0

        while True:
            success, frame = cap.read()

            if not success:
                break

            if frame_number % self.interval == 0:
                filename = os.path.join(self.output_folder, f"frame_{saved:05d}.jpg")

                cv2.imwrite(filename, frame)
                saved += 1

            frame_number += 1

        cap.release()

        print(f"Saved {saved} frames.")

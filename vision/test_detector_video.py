import cv2
import os

from vision.detector import Detector
from vision.visualizer import Visualizer
from configs.settings import MODEL_PATH

VIDEO_PATH = "replays/game1.mp4"
OUTPUT_PATH = "data/processed/detected_game1.mp4"


def main():

    detector = Detector(MODEL_PATH)

    visualizer = Visualizer()

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print("Could not open video.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    os.makedirs("data/processed", exist_ok=True)

    writer = cv2.VideoWriter(
        OUTPUT_PATH,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    frame_count = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        detections = detector.detect(frame)

        output = visualizer.draw(frame, detections)

        writer.write(output)

        print(f"Frame {frame_count:04d} | " f"Detections: {len(detections)}")

        frame_count += 1

    cap.release()
    writer.release()

    print("\nDone!")
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()

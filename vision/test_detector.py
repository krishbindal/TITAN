import cv2
import glob
import os

from vision.detector import Detector
from vision.visualizer import Visualizer
from configs.settings import MODEL_PATH


def main():

    detector = Detector(MODEL_PATH)

    visualizer = Visualizer()

    # Find all extracted frames
    images = sorted(glob.glob(os.path.join("data", "raw", "*.jpg")))

    if not images:
        print("No images found in data/raw")
        return

    print("=" * 60)
    print(f"Found {len(images)} frame(s)")
    print("=" * 60)

    while True:
        try:
            index = int(input(f"Choose frame (0-{len(images)-1}): "))

            if 0 <= index < len(images):
                break

            print("Invalid frame number.\n")

        except ValueError:
            print("Please enter a valid number.\n")

    image_path = images[index]

    print("\nLoading:", image_path)

    frame = cv2.imread(image_path)

    if frame is None:
        print("Error: Could not load image.")
        return

    detections = detector.detect(frame)

    print("\n" + "=" * 60)
    print(f"Detected {len(detections)} object(s)")
    print("=" * 60)

    if len(detections) == 0:
        print("No detections.")

    for detection in detections:
        print(detection)

    output = visualizer.draw(frame, detections)

    os.makedirs("data/processed", exist_ok=True)

    filename = os.path.basename(image_path)

    output_path = os.path.join("data", "processed", f"detected_{filename}")

    cv2.imwrite(output_path, output)

    print("\nSaved result to:")
    print(output_path)

    cv2.imshow("Titan Detection", output)

    cv2.waitKey(0)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

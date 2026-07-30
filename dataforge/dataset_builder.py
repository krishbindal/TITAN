import os
import cv2

from vision.detector import Detector
from vision.region_filter import RegionFilter
from dataforge.active_learning import ActiveLearning
from configs.settings import (
    MODEL_PATH,
    AUTO_LABEL_CONFIDENCE,
    AUTO_LABELED_DIR,
    EXTRACTED_FRAMES_DIR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class DatasetBuilder:

    def __init__(self, model_path=None, confidence_threshold=None):

        self.model_path = model_path or MODEL_PATH

        self.detector = Detector(self.model_path)

        self.region_filter = RegionFilter()

        self.active_learning = ActiveLearning(
            threshold=confidence_threshold or AUTO_LABEL_CONFIDENCE
        )

        self.output_dir = AUTO_LABELED_DIR

        # Class names from the model
        self.class_names = list(self.detector.model.names.values())

    def label_frame(self, frame):
        """Run detection on a frame and return labels in YOLO format."""

        detections = self.detector.detect(frame)

        detections = self.region_filter.filter(detections)

        labels = []

        h, w = frame.shape[:2]

        for det in detections:

            class_id = self._get_class_id(det.name)

            if class_id is None:
                continue

            # Convert to YOLO format (normalized)
            x_center = (det.x + det.width / 2) / w
            y_center = (det.y + det.height / 2) / h
            box_width = det.width / w
            box_height = det.height / h

            # Clamp to [0, 1]
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            box_width = max(0.0, min(1.0, box_width))
            box_height = max(0.0, min(1.0, box_height))

            labels.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} "
                f"{box_width:.6f} {box_height:.6f}"
            )

        return labels, detections

    def process_folder(self, input_dir=None):
        """Auto-label all extracted frames."""

        input_dir = input_dir or EXTRACTED_FRAMES_DIR

        accepted_dir = os.path.join(self.output_dir, "accepted")
        review_dir = os.path.join(self.output_dir, "review")
        empty_dir = os.path.join(self.output_dir, "empty")

        for d in [accepted_dir, review_dir, empty_dir]:
            os.makedirs(os.path.join(d, "images"), exist_ok=True)
            os.makedirs(os.path.join(d, "labels"), exist_ok=True)

        stats = {"accepted": 0, "review": 0, "empty": 0, "total": 0}

        # Find all image files across all video subdirectories
        image_files = []

        for root, dirs, files in os.walk(input_dir):

            for f in sorted(files):

                if f.lower().endswith((".jpg", ".jpeg", ".png")):
                    image_files.append(os.path.join(root, f))

        print(f"Found {len(image_files)} images to label")
        print("=" * 60)

        for i, image_path in enumerate(image_files):

            frame = cv2.imread(image_path)

            if frame is None:
                continue

            labels, detections = self.label_frame(frame)

            # Determine routing
            base_name = f"frame_{stats['total']:06d}"

            if len(labels) == 0:
                dest_dir = empty_dir
                stats["empty"] += 1

            elif self.active_learning.needs_review(detections):
                dest_dir = review_dir
                stats["review"] += 1

            else:
                dest_dir = accepted_dir
                stats["accepted"] += 1

            # Save image
            img_path = os.path.join(dest_dir, "images", f"{base_name}.jpg")
            cv2.imwrite(img_path, frame)

            # Save label
            if labels:
                label_path = os.path.join(dest_dir, "labels", f"{base_name}.txt")
                with open(label_path, "w") as f:
                    f.write("\n".join(labels))

            stats["total"] += 1

            if (i + 1) % 100 == 0:
                print(
                    f"  Processed {i+1}/{len(image_files)} | "
                    f"Accepted: {stats['accepted']} | "
                    f"Review: {stats['review']} | "
                    f"Empty: {stats['empty']}"
                )

        print("=" * 60)
        print(f"DONE: {stats['total']} images processed")
        print(f"  Accepted (auto-labeled): {stats['accepted']}")
        print(f"  Needs review:            {stats['review']}")
        print(f"  Empty (no detections):   {stats['empty']}")

        return stats

    def _get_class_id(self, name):

        try:
            return self.class_names.index(name)
        except ValueError:
            return None


if __name__ == "__main__":

    builder = DatasetBuilder()
    builder.process_folder()

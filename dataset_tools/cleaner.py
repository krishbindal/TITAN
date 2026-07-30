import os
import cv2


class DatasetCleaner:

    def __init__(self, dataset_dir, num_classes=103):

        self.dataset_dir = dataset_dir
        self.num_classes = num_classes

    def validate(self, split="train"):
        """Run all validation checks on a dataset split."""

        img_dir = os.path.join(self.dataset_dir, split, "images")
        label_dir = os.path.join(self.dataset_dir, split, "labels")

        issues = {
            "missing_labels": [],
            "missing_images": [],
            "corrupt_images": [],
            "invalid_labels": [],
            "out_of_range_classes": [],
        }

        if not os.path.exists(img_dir):
            print(f"Image directory not found: {img_dir}")
            return issues

        # Get all image and label files
        images = set(
            os.path.splitext(f)[0]
            for f in os.listdir(img_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )

        labels = set()
        if os.path.exists(label_dir):
            labels = set(
                os.path.splitext(f)[0]
                for f in os.listdir(label_dir)
                if f.endswith(".txt")
            )

        # Check for images without labels
        for name in images - labels:
            issues["missing_labels"].append(name)

        # Check for labels without images
        for name in labels - images:
            issues["missing_images"].append(name)

        # Check for corrupt images
        for name in images:

            for ext in [".jpg", ".jpeg", ".png"]:

                path = os.path.join(img_dir, name + ext)

                if os.path.exists(path):

                    img = cv2.imread(path)

                    if img is None:
                        issues["corrupt_images"].append(name + ext)

                    break

        # Validate label format
        for name in labels:

            label_path = os.path.join(label_dir, name + ".txt")

            with open(label_path, "r") as f:

                for line_num, line in enumerate(f, 1):

                    parts = line.strip().split()

                    if len(parts) == 0:
                        continue

                    if len(parts) != 5:
                        issues["invalid_labels"].append(
                            f"{name}.txt line {line_num}: "
                            f"expected 5 values, got {len(parts)}"
                        )
                        continue

                    try:
                        class_id = int(parts[0])
                        values = [float(p) for p in parts[1:]]

                        if class_id < 0 or class_id >= self.num_classes:
                            issues["out_of_range_classes"].append(
                                f"{name}.txt: class {class_id} "
                                f"(max: {self.num_classes - 1})"
                            )

                        for v in values:
                            if v < 0.0 or v > 1.0:
                                issues["invalid_labels"].append(
                                    f"{name}.txt line {line_num}: "
                                    f"value {v} out of range [0,1]"
                                )
                                break

                    except ValueError:
                        issues["invalid_labels"].append(
                            f"{name}.txt line {line_num}: " f"non-numeric values"
                        )

        return issues

    def report(self, split="train"):
        """Print a validation report."""

        issues = self.validate(split)

        print(f"\n=== Data Quality Report ({split}) ===")

        total_issues = sum(len(v) for v in issues.values())

        if total_issues == 0:
            print("All checks passed. No issues found.")
            return issues

        for category, items in issues.items():

            if items:
                print(f"\n{category} ({len(items)}):")
                for item in items[:10]:
                    print(f"  - {item}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")

        print(f"\nTotal issues: {total_issues}")

        return issues

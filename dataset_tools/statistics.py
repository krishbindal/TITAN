import os


class DatasetStatistics:

    def __init__(self, dataset_dir, class_names=None):

        self.dataset_dir = dataset_dir
        self.class_names = class_names or []

    def count_images(self, split="train"):

        img_dir = os.path.join(self.dataset_dir, split, "images")

        if not os.path.exists(img_dir):
            return 0

        return len(
            [
                f
                for f in os.listdir(img_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )

    def count_per_class(self, split="train"):
        """Count annotations per class."""

        label_dir = os.path.join(self.dataset_dir, split, "labels")

        counts = {}

        if not os.path.exists(label_dir):
            return counts

        for filename in os.listdir(label_dir):

            if not filename.endswith(".txt"):
                continue

            filepath = os.path.join(label_dir, filename)

            with open(filepath, "r") as f:

                for line in f:

                    parts = line.strip().split()

                    if len(parts) >= 5:

                        class_id = int(parts[0])

                        name = self._id_to_name(class_id)

                        counts[name] = counts.get(name, 0) + 1

        return counts

    def find_underrepresented(self, split="train", min_count=20):
        """Find classes with fewer than min_count annotations."""

        counts = self.count_per_class(split)

        under = []

        for name in self.class_names:

            count = counts.get(name, 0)

            if count < min_count:
                under.append({"name": name, "count": count})

        under.sort(key=lambda x: x["count"])

        return under

    def report(self, split="train"):
        """Print a full dataset report."""

        counts = self.count_per_class(split)
        total_images = self.count_images(split)
        total_annotations = sum(counts.values())

        print(f"\n=== Dataset Report ({split}) ===")
        print(f"Total images: {total_images}")
        print(f"Total annotations: {total_annotations}")
        print(f"Classes with data: {len(counts)}/{len(self.class_names)}")

        if counts:
            print(f"\n{'Class':<35} {'Count':>8}")
            print("-" * 45)

            for name in sorted(counts.keys(), key=lambda x: counts[x], reverse=True):
                print(f"{name:<35} {counts[name]:>8}")

        under = self.find_underrepresented(split)

        if under:
            print(f"\n⚠ Underrepresented classes (< 20 annotations):")
            for cls in under:
                print(f"  {cls['name']}: {cls['count']}")

    def _id_to_name(self, class_id):

        if 0 <= class_id < len(self.class_names):
            return self.class_names[class_id]

        return f"unknown_{class_id}"

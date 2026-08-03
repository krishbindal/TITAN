import os
import shutil
import random


class DatasetManager:

    def __init__(self, dataset_dir):

        self.dataset_dir = dataset_dir

    def merge(self, source_dir, target_split="train"):
        """Merge auto-labeled data into the main dataset."""

        src_images = os.path.join(source_dir, "images")
        src_labels = os.path.join(source_dir, "labels")

        dst_images = os.path.join(self.dataset_dir, target_split, "images")
        dst_labels = os.path.join(self.dataset_dir, target_split, "labels")

        os.makedirs(dst_images, exist_ok=True)
        os.makedirs(dst_labels, exist_ok=True)

        copied = 0

        if not os.path.exists(src_images):
            print(f"Source directory not found: {src_images}")
            return 0

        for filename in os.listdir(src_images):

            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            base = os.path.splitext(filename)[0]
            label_file = base + ".txt"

            # Check if label exists
            src_label_path = os.path.join(src_labels, label_file)

            if not os.path.exists(src_label_path):
                continue

            # Generate unique name to avoid conflicts
            dst_name = f"auto_{base}"

            # Copy image
            shutil.copy2(
                os.path.join(src_images, filename),
                os.path.join(dst_images, f"{dst_name}.jpg"),
            )

            # Copy label
            shutil.copy2(src_label_path, os.path.join(dst_labels, f"{dst_name}.txt"))

            copied += 1

        print(f"Merged {copied} labeled images into {target_split}")

        return copied

    def split(self, source_dir, train_ratio=0.80, val_ratio=0.15):
        """Split a flat image+label directory into train/val/test."""

        img_dir = os.path.join(source_dir, "images")
        label_dir = os.path.join(source_dir, "labels")

        if not os.path.exists(img_dir):
            print(f"Source images not found: {img_dir}")
            return

        # Find all images with matching labels
        pairs = []

        for filename in os.listdir(img_dir):

            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            base = os.path.splitext(filename)[0]
            label_path = os.path.join(label_dir, base + ".txt")

            if os.path.exists(label_path):
                pairs.append((filename, base + ".txt"))

        random.shuffle(pairs)

        n = len(pairs)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        splits = {
            "train": pairs[:train_end],
            "valid": pairs[train_end:val_end],
            "test": pairs[val_end:],
        }

        for split_name, split_pairs in splits.items():

            split_img = os.path.join(self.dataset_dir, split_name, "images")
            split_label = os.path.join(self.dataset_dir, split_name, "labels")

            os.makedirs(split_img, exist_ok=True)
            os.makedirs(split_label, exist_ok=True)

            for img_file, label_file in split_pairs:

                shutil.copy2(
                    os.path.join(img_dir, img_file), os.path.join(split_img, img_file)
                )

                shutil.copy2(
                    os.path.join(label_dir, label_file),
                    os.path.join(split_label, label_file),
                )

        print(
            f"Split {n} pairs: "
            f"train={len(splits['train'])}, "
            f"val={len(splits['valid'])}, "
            f"test={len(splits['test'])}"
        )

    def backup(self, backup_name="backup"):
        """Backup the current dataset."""

        backup_dir = os.path.join(
            os.path.dirname(self.dataset_dir),
            f"{os.path.basename(self.dataset_dir)}_{backup_name}",
        )

        if os.path.exists(backup_dir):
            print(f"Backup already exists: {backup_dir}")
            return

        shutil.copytree(self.dataset_dir, backup_dir)

        print(f"Backed up to: {backup_dir}")

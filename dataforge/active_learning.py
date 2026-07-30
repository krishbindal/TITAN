class ActiveLearning:

    def __init__(self, threshold=0.75):

        self.threshold = threshold

        # Track per-class confidence stats
        self.class_stats = {}

    def needs_review(self, detections):

        if not detections:
            return True

        lowest = min(d.confidence for d in detections)

        # Record stats
        for det in detections:
            self._record(det)

        return lowest < self.threshold

    def get_weak_classes(self, min_samples=5):
        """Return classes that consistently trigger review."""

        weak = []

        for name, stats in self.class_stats.items():

            if stats["count"] < min_samples:
                continue

            avg_conf = stats["total_confidence"] / stats["count"]

            if avg_conf < self.threshold:
                weak.append(
                    {
                        "name": name,
                        "avg_confidence": round(avg_conf, 3),
                        "count": stats["count"],
                        "below_threshold": stats["below_threshold"],
                    }
                )

        weak.sort(key=lambda x: x["avg_confidence"])

        return weak

    def report(self):
        """Print a summary of class confidence stats."""

        print("\n=== Active Learning Report ===")

        weak = self.get_weak_classes()

        if not weak:
            print("No consistently weak classes found.")
            return

        print(f"\nWeak classes (avg confidence < {self.threshold}):")
        print(f"{'Class':<35} {'Avg Conf':>10} {'Count':>8} {'Below':>8}")
        print("-" * 65)

        for cls in weak:
            print(
                f"{cls['name']:<35} "
                f"{cls['avg_confidence']:>10.3f} "
                f"{cls['count']:>8} "
                f"{cls['below_threshold']:>8}"
            )

    def _record(self, detection):

        name = detection.name

        if name not in self.class_stats:
            self.class_stats[name] = {
                "count": 0,
                "total_confidence": 0.0,
                "below_threshold": 0,
            }

        self.class_stats[name]["count"] += 1
        self.class_stats[name]["total_confidence"] += detection.confidence

        if detection.confidence < self.threshold:
            self.class_stats[name]["below_threshold"] += 1

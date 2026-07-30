import os

from ultralytics import YOLO


class ModelEvaluator:

    def __init__(self, model_path):

        self.model = YOLO(model_path)
        self.model_path = model_path

    def evaluate(self, data_yaml="datasets/data.yaml", imgsz=640):
        """Run full evaluation on the test set."""

        print("=" * 60)
        print(f"Evaluating: {self.model_path}")
        print("=" * 60)

        results = self.model.val(
            data=data_yaml, imgsz=imgsz, split="test", plots=True, save_json=True
        )

        return results

    def per_class_analysis(self, data_yaml="datasets/data.yaml"):
        """Analyze per-class performance."""

        results = self.model.val(data=data_yaml, split="test")

        names = self.model.names

        print("\n=== Per-Class mAP@50 ===")
        print(f"{'Class':<35} {'mAP@50':>10} {'Precision':>10} {'Recall':>10}")
        print("-" * 70)

        class_results = []

        ap50 = results.box.ap50

        for i, (class_id, name) in enumerate(names.items()):

            if i < len(ap50):

                score = float(ap50[i])

                class_results.append({"name": name, "map50": score})

        # Sort by mAP (worst first)
        class_results.sort(key=lambda x: x["map50"])

        for cls in class_results:
            indicator = "⚠" if cls["map50"] < 0.30 else " "
            print(f"{indicator} {cls['name']:<33} {cls['map50']:>10.3f}")

        # Summary
        weak = [c for c in class_results if c["map50"] < 0.30]

        if weak:
            print(f"\n⚠ {len(weak)} classes below 0.30 mAP:")
            for c in weak:
                print(f"  - {c['name']}: {c['map50']:.3f}")
            print("\nRecommendation: Collect more training data for these classes.")

        return class_results

    def compare(self, other_model_path, data_yaml="datasets/data.yaml"):
        """Compare this model against another model."""

        print("\n=== Model Comparison ===")

        # Evaluate this model
        print(f"\nModel A: {self.model_path}")
        results_a = self.model.val(data=data_yaml, split="test")

        # Evaluate other model
        print(f"\nModel B: {other_model_path}")
        other = YOLO(other_model_path)
        results_b = other.val(data=data_yaml, split="test")

        map50_a = float(results_a.box.map50)
        map50_b = float(results_b.box.map50)

        map_a = float(results_a.box.map)
        map_b = float(results_b.box.map)

        print(f"\n{'Metric':<20} {'Model A':>12} {'Model B':>12} {'Diff':>12}")
        print("-" * 60)
        print(
            f"{'mAP@50':<20} {map50_a:>12.3f} {map50_b:>12.3f} {map50_a - map50_b:>+12.3f}"
        )
        print(
            f"{'mAP@50-95':<20} {map_a:>12.3f} {map_b:>12.3f} {map_a - map_b:>+12.3f}"
        )

        winner = "Model A" if map50_a > map50_b else "Model B"
        print(f"\nWinner: {winner}")


if __name__ == "__main__":

    evaluator = ModelEvaluator("models/best.pt")
    evaluator.per_class_analysis()

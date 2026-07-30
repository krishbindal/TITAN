"""
TITAN — Google Colab Training Script

Usage:
  1. Upload your dataset to Google Drive
  2. Open this script in Google Colab
  3. Enable GPU: Runtime → Change runtime type → T4 GPU
  4. Run all cells
"""

import os
import torch
from ultralytics import YOLO


def check_environment():
    """Verify GPU and environment."""

    print("=" * 60)
    print("TITAN Training Environment Check")
    print("=" * 60)

    # GPU check
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"GPU: {gpu_name} ({gpu_mem:.1f} GB)")
    else:
        print("WARNING: No GPU detected!")
        print("Go to Runtime → Change runtime type → T4 GPU")
        return False

    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.version.cuda}")
    print("=" * 60)

    return True


def mount_drive():
    """Mount Google Drive (only works in Colab)."""

    try:
        from google.colab import drive

        drive.mount("/content/drive")
        print("Google Drive mounted.")
        return True
    except ImportError:
        print("Not running in Colab — skipping Drive mount.")
        return False


def train(
    data_yaml="datasets/data.yaml",
    model_name="yolo11s.pt",
    epochs=150,
    batch=16,
    imgsz=640,
    project="runs/train",
    name="titan_colab",
):
    """Run optimized YOLO training."""

    if not check_environment():
        print("\nAborting: Fix GPU setup first.")
        return

    print(f"\nLoading model: {model_name}")
    model = YOLO(model_name)

    print(f"Dataset: {data_yaml}")
    print(f"Training for {epochs} epochs...")
    print("=" * 60)

    results = model.train(
        # Dataset
        data=data_yaml,
        # Training duration
        epochs=epochs,
        patience=30,
        # Batch and image size
        imgsz=imgsz,
        batch=batch,
        # Device
        device=0,
        # Optimizer
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=5,
        cos_lr=True,
        # Augmentation — game-specific
        # NEVER flip: Clash Royale has meaningful orientation
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.3,
        degrees=0,
        translate=0.1,
        scale=0.3,
        flipud=0.0,
        fliplr=0.0,
        mosaic=1.0,
        mixup=0.1,
        close_mosaic=20,
        # Regularization
        label_smoothing=0.05,
        # Loss weights
        cls=1.0,
        box=7.5,
        # Validation and saving
        val=True,
        plots=True,
        save_period=25,
        # Performance
        workers=2,
        cache="disk",
        # Project
        project=project,
        name=name,
    )

    # Print results
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)

    # Find best model
    best_path = os.path.join(project, name, "weights", "best.pt")

    if os.path.exists(best_path):
        print(f"Best model saved to: {best_path}")
        size_mb = os.path.getsize(best_path) / 1024 / 1024
        print(f"Model size: {size_mb:.1f} MB")

    return results


if __name__ == "__main__":
    train()

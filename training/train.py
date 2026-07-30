from ultralytics import YOLO


def train():

    # Upgrade from YOLO11 Nano to Small for 103 classes
    model = YOLO("yolo11s.pt")

    model.train(
        # Dataset
        data="datasets/data.yaml",
        # Training duration
        epochs=150,
        patience=30,
        # Batch and image size
        imgsz=640,
        batch=16,
        # Device
        device=0,
        # Optimizer
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=5,
        cos_lr=True,
        # Augmentation — game-specific
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
        project="runs/train",
        name="titan_v2",
    )


if __name__ == "__main__":
    train()

import torch
from ultralytics import YOLO
from tracker.detection import Detection


class Detector:

    def __init__(self, model_path, confidence=0.4):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.device = "0" if torch.cuda.is_available() else "cpu"
        self.half = torch.cuda.is_available()

    def detect(self, frame):

        detections = []

        results = self.model(
            frame,
            conf=self.confidence,
            device=self.device,
            half=self.half,
            verbose=False,
        )

        for result in results:

            for box in result.boxes:

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                confidence = float(box.conf[0])

                class_id = int(box.cls[0])

                name = self.model.names[class_id]

                detection = Detection(
                    name=name,
                    x=x1,
                    y=y1,
                    width=x2 - x1,
                    height=y2 - y1,
                    confidence=confidence,
                )

                detections.append(detection)

        return detections

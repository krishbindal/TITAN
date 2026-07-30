import cv2


class VideoInfo:

    def __init__(self, video_path):

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

    def get_info(self):

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        duration = frame_count / fps if fps > 0 else 0

        return {
            "fps": fps,
            "frames": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "duration_min": round(duration / 60, 1),
        }

    def is_valid(self):

        if not self.cap.isOpened():
            return False

        info = self.get_info()

        if info["fps"] <= 0 or info["frames"] <= 0:
            return False

        if info["width"] <= 0 or info["height"] <= 0:
            return False

        return True

    def release(self):

        self.cap.release()

    def __str__(self):

        info = self.get_info()

        return (
            f"{self.video_path} | "
            f"{info['width']}x{info['height']} | "
            f"{info['fps']:.0f} fps | "
            f"{info['duration_min']} min"
        )

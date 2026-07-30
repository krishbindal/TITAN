import cv2


class Replay:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

    def read_frame(self):
        """
        Returns:
            success (bool)
            frame (numpy.ndarray)
        """
        return self.cap.read()

    def reset(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def release(self):
        self.cap.release()

    def fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    def frame_count(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

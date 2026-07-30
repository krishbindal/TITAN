import cv2


class DuplicateFilter:

    def __init__(self, threshold=8):
        self.previous = None
        self.threshold = threshold

    def should_save(self, frame):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.previous is None:
            self.previous = gray
            return True

        diff = cv2.absdiff(self.previous, gray)

        score = diff.mean()

        if score > self.threshold:
            self.previous = gray
            return True

        return False

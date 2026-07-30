"""
OCR-based Level Reader for detecting troop levels from bounding boxes.
Uses EasyOCR to read the small level number on each troop.
"""

import cv2
import numpy as np


class LevelReader:
    """
    Reads the level number from a troop's bounding box.
    The level badge in Clash Royale appears as a small colored circle
    with a white number, positioned at the top-left of each unit.
    """

    def __init__(self):
        self._ocr = None  # Lazy-load EasyOCR (it is heavy)
        self.default_level = 11

    def _get_ocr(self):
        """Lazy-load EasyOCR on first use to avoid slow startup."""
        if self._ocr is None:
            import easyocr

            self._ocr = easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._ocr

    def read_level(self, frame, x, y, w, h):
        """
        Read the level from a troop's bounding box region.

        Args:
            frame: Full game frame (BGR image)
            x, y: Top-left corner of the bounding box
            w, h: Width and height of the bounding box

        Returns:
            int: The detected level (1-16), or default_level if unreadable.
        """
        try:
            # The level badge sits at the top-left of the bounding box.
            # Crop a small region around it.
            badge_x = max(0, int(x) - 5)
            badge_y = max(0, int(y) - 5)
            badge_w = min(int(w * 0.35), 40)
            badge_h = min(int(h * 0.2), 30)

            crop = frame[badge_y : badge_y + badge_h, badge_x : badge_x + badge_w]

            if crop.size == 0:
                return self.default_level

            # Upscale the tiny crop for better OCR accuracy
            scale = 4
            crop = cv2.resize(
                crop,
                (crop.shape[1] * scale, crop.shape[0] * scale),
                interpolation=cv2.INTER_CUBIC,
            )

            # Convert to grayscale and threshold to isolate white text
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

            # Run OCR
            ocr = self._get_ocr()
            results = ocr.readtext(thresh, allowlist="0123456789", detail=0)

            # Parse the first valid number
            for text in results:
                text = text.strip()
                if text.isdigit():
                    level = int(text)
                    if 1 <= level <= 16:
                        return level

            return self.default_level

        except Exception:
            return self.default_level

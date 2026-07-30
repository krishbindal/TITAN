import cv2
import pytesseract
import numpy as np
import traceback

from ui_reader.ui_state import UIState
from configs.settings import SCREEN_HEIGHT, SCREEN_WIDTH


class UIReader:
    def __init__(self):
        # Configure tesseract for single digits/numbers
        self.tess_config = '--psm 7 -c tessedit_char_whitelist=0123456789.'
        # Windows default Tesseract path (user must install this)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def read(self, frame):
        """
        Extracts the player's elixir from the bottom of the screen using OCR.
        """
        state = UIState()
        
        try:
            # Crop the bottom elixir bar area
            # (Roughly the bottom 80 pixels, centered horizontally)
            y_start = SCREEN_HEIGHT - 80
            y_end = SCREEN_HEIGHT
            x_start = int(SCREEN_WIDTH * 0.2)
            x_end = int(SCREEN_WIDTH * 0.8)
            
            crop = frame[y_start:y_end, x_start:x_end]
            
            if crop is not None and crop.size > 0:
                # Preprocess for better OCR (grayscale -> threshold)
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                # Tesseract works best with dark text on light background
                # The CR elixir text is pink/purple on dark, so we threshold and invert
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
                
                text = pytesseract.image_to_string(thresh, config=self.tess_config).strip()
                
                if text:
                    try:
                        elixir_val = float(text)
                        # Sanity check: elixir is 0 to 10
                        if 0 <= elixir_val <= 10:
                            state.player_elixir = elixir_val
                    except ValueError:
                        pass
        except Exception as e:
            # Silently fail if Tesseract is not installed, it will fall back to time-based
            pass

        return state

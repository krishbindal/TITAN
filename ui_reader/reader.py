import cv2
import numpy as np
import traceback
import time
import pytesseract

from ui_reader.ui_state import UIState
from configs.settings import SCREEN_HEIGHT, SCREEN_WIDTH


class UIReader:
    def __init__(self):
        # Tesseract is only used for throttled Tower HP checks now
        self.last_hp_check = 0.0
        self.hp_check_interval = 1.0  # seconds between OCR reads
        self.cached_left_hp = None
        self.cached_right_hp = None
        self.tesseract_available = True

    def read(self, frame):
        """
        Extracts the player's elixir from the bottom of the screen using fast HSV pixel counting.
        """
        state = UIState()
        
        try:
            # Crop the bottom elixir bar area
            # Elixir bar is roughly at the bottom, centered horizontally
            y_start = SCREEN_HEIGHT - 60
            y_end = SCREEN_HEIGHT - 10
            x_start = int(SCREEN_WIDTH * 0.15)
            x_end = int(SCREEN_WIDTH * 0.85)
            
            crop = frame[y_start:y_end, x_start:x_end]
            
            if crop is not None and crop.size > 0:
                # Convert to HSV for robust color filtering
                hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                
                # Pink/Purple elixir bar bounds
                lower_pink = np.array([135, 100, 150])
                upper_pink = np.array([170, 255, 255])
                
                mask = cv2.inRange(hsv, lower_pink, upper_pink)
                
                # Find the rightmost pink pixel
                coords = cv2.findNonZero(mask)
                if coords is not None:
                    max_x = np.max(coords[..., 0])
                    # Total possible width of the elixir bar crop
                    total_width = crop.shape[1]
                    
                    # Elixir fills from left to right (0 to 10)
                    percentage = max_x / total_width
                    elixir_val = percentage * 10.0
                    
                    # Sanity check: elixir is 0 to 10
                    state.player_elixir = min(10.0, max(0.0, elixir_val))
                else:
                    # No pink found -> 0 elixir
                    state.player_elixir = 0.0
        except Exception as e:
            print(f"[UIReader] Error reading elixir: {e}")

        # Phase 6: Throttled Tower HP OCR
        current_time = time.time()
        if self.tesseract_available and (current_time - self.last_hp_check > self.hp_check_interval):
            self.last_hp_check = current_time
            try:
                # Approximate bounding boxes for enemy princess towers
                left_crop = frame[190:230, 110:250]
                right_crop = frame[190:230, 470:610]
                
                # Preprocess for OCR (grayscale, threshold)
                left_gray = cv2.cvtColor(left_crop, cv2.COLOR_BGR2GRAY)
                right_gray = cv2.cvtColor(right_crop, cv2.COLOR_BGR2GRAY)
                _, left_thresh = cv2.threshold(left_gray, 200, 255, cv2.THRESH_BINARY)
                _, right_thresh = cv2.threshold(right_gray, 200, 255, cv2.THRESH_BINARY)
                
                # OCR config for digits only
                config = '--psm 7 -c tessedit_char_whitelist=0123456789'
                
                l_text = pytesseract.image_to_string(left_thresh, config=config).strip()
                if l_text and l_text.isdigit():
                    self.cached_left_hp = int(l_text)
                    
                r_text = pytesseract.image_to_string(right_thresh, config=config).strip()
                if r_text and r_text.isdigit():
                    self.cached_right_hp = int(r_text)
            except pytesseract.TesseractNotFoundError:
                print("[UIReader] Tesseract OCR not found. Disabling Tower HP checks.")
                self.tesseract_available = False
            except Exception as e:
                print(f"[UIReader] Error reading tower HP: {e}")
                
        state.enemy_left_tower_hp = self.cached_left_hp
        state.enemy_right_tower_hp = self.cached_right_hp

        return state

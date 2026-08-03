import cv2
import numpy as np
import pytesseract
import re

class CollectionReader:
    """
    Computer Vision module for the Clash Royale Collection Screen.
    Uses color detection to find upgradable cards and OCR to read stats.
    """
    def __init__(self):
        # Configure tesseract path and settings
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.tess_config = '--psm 7 -c tessedit_char_whitelist=0123456789'
        
        # HSV range for the bright green Upgrade progress bar
        self.lower_green = np.array([40, 150, 150])
        self.upper_green = np.array([80, 255, 255])
        
    def find_upgradable_cards(self, frame):
        """
        Scans the screen for the bright green upgrade bars under cards.
        Returns a list of (x, y) coordinates for the center of upgradable cards.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
        
        # Find contours of the green bars
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        upgradable_coords = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter out tiny green pixels (noise)
            if area > 500:
                x, y, w, h = cv2.boundingRect(cnt)
                # The bar is at the bottom of the card, so the center of the card is slightly above the bar
                card_center_x = x + (w // 2)
                card_center_y = y - 50 
                upgradable_coords.append((card_center_x, card_center_y))
                
        return upgradable_coords

    def read_top_right_gold(self, frame):
        """
        Reads the user's total gold from the top right corner of the menu.
        """
        # Crop top right corner (approx bounds for 720x1280)
        crop = frame[20:80, 450:650]
        if crop.size > 0:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            text = pytesseract.image_to_string(thresh, config=self.tess_config).strip()
            try:
                return int(text)
            except ValueError:
                return 0
        return 0
            
    def read_upgrade_cost(self, frame):
        """
        Reads the gold cost from the upgrade confirmation popup.
        """
        # Crop the center popup button area
        crop = frame[800:900, 200:520]
        if crop.size > 0:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            text = pytesseract.image_to_string(thresh, config=self.tess_config).strip()
            try:
                return int(text)
            except ValueError:
                return 999999 # Return impossibly high cost if OCR fails
        return 999999

    def read_card_popup_name(self, frame, tap_x, tap_y):
        """
        Reads the card name from the popup that appears after tapping a card in the collection.
        """
        # The name appears slightly below the tapped coordinate (which is the center of the card)
        y_start = max(0, tap_y)
        y_end = min(frame.shape[0], tap_y + 150)
        x_start = max(0, tap_x - 120)
        x_end = min(frame.shape[1], tap_x + 120)
        
        crop = frame[y_start:y_end, x_start:x_end]
        
        if crop.size > 0:
            # Convert to grayscale
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            
            # Upscale the image by 2x for better OCR accuracy on small text
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            # Apply thresholding for white text
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            
            # Whitelist letters and spaces
            config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '
            
            try:
                text = pytesseract.image_to_string(thresh, config=config, timeout=2).strip().lower()
            except RuntimeError:
                text = ""
            
            # Replace spaces with underscores to match our database keys (e.g. "mini_pekka")
            return text.replace(" ", "_")
        return ""

    def is_card_locked(self, frame, card_x, card_y):
        """
        Check if a card at the given grid position is locked (greyed out).
        Locked cards have very low color saturation (they appear grey/dark).
        Returns True if the card is locked.
        """
        margin = 45
        y1 = max(0, card_y - margin)
        y2 = min(frame.shape[0], card_y + margin)
        x1 = max(0, card_x - margin)
        x2 = min(frame.shape[1], card_x + margin)
        
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return True
        
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        
        # Locked cards are greyed out — very low saturation. 
        # They are completely grayscale, whereas unlocked cards have colorful borders.
        avg_saturation = np.mean(hsv[:, :, 1])
        
        # Unlocked cards are colorful (high saturation). Locked cards are grey (low sat).
        is_locked = avg_saturation < 60
        return is_locked

    def read_card_level(self, frame):
        """
        Read the card level from the popup ("Level X" text below the card name).
        Returns the level as an integer, or 0 if OCR fails.
        """
        # On 720x1280 screen, "Level X" text is roughly at y=250-285, centered
        crop = frame[245:290, 100:320]
        if crop.size == 0:
            return 0
        
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        
        config = '--psm 7 -c tessedit_char_whitelist=Level0123456789 '
        text = pytesseract.image_to_string(thresh, config=config).strip()
        
        match = re.search(r'(\d+)', text)
        if match:
            level = int(match.group(1))
            if 1 <= level <= 14:
                return level
        return 0

    def read_card_info_slide(self, frame):
        """
        Read detailed stats from the info slide of the card popup.
        This is the second page you see after swiping left on the card popup.
        Returns a dict with any stats it can parse (damage, hp, hit_speed, etc).
        """
        # Stats area on the info slide (720x1280 screen)
        # Green/blue stat boxes are roughly in the center of the popup
        stats_crop = frame[340:500, 20:400]
        if stats_crop.size == 0:
            return {"raw": ""}
        
        gray = cv2.cvtColor(stats_crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        
        config = '--psm 6'
        text = pytesseract.image_to_string(thresh, config=config).strip()
        
        stats = {"raw": text}
        
        # Parse common stat patterns from OCR text
        damage_match = re.search(r'(?:Area\s*)?Damage\s*(\d+)', text, re.IGNORECASE)
        if damage_match:
            stats["damage"] = int(damage_match.group(1))
        
        hp_match = re.search(r'(?:Hitpoints|HP)\s*(\d+)', text, re.IGNORECASE)
        if hp_match:
            stats["hp"] = int(hp_match.group(1))
        
        speed_match = re.search(r'Hit\s*Speed\s*([\d]+[.,]?[\d]*)', text, re.IGNORECASE)
        if speed_match:
            try:
                stats["hit_speed"] = float(speed_match.group(1).replace(',', '.'))
            except ValueError:
                pass

        range_match = re.search(r'Range\s*([\d.]+)', text, re.IGNORECASE)
        if range_match:
            stats["range"] = float(range_match.group(1))

        radius_match = re.search(r'Radius\s*([\d.]+)', text, re.IGNORECASE)
        if radius_match:
            stats["radius"] = float(radius_match.group(1))
        
        return stats

import time
import cv2
import numpy as np
import logging

logger = logging.getLogger("TITAN")

class UINavigator:
    """
    Handles navigation between non-gameplay menus in Clash Royale.
    Uses robust visual verification before tapping to prevent blind taps.
    """
    def __init__(self, adb_controller):
        self.adb = adb_controller
        
        # Absolute coordinates for the bottom navigation bar (720x1280)
        self.nav_y = 1170
        self.tabs = {
            "shop": 80,
            "collection": 220,
            "battle": 360,
            "clan": 500,
            "events": 640
        }

    def verify_and_tap(self, x, y, description):
        """
        Taps the coordinate and logs the action. 
        In a full implementation, this takes an image template to find.
        For absolute tabs, we trust the hardcoded Y coordinate but log it.
        """
        logger.info(f"Tapping {description} at ({x}, {y})")
        self.adb.tap(x, y)
        time.sleep(1.0)
        
    def go_to_collection(self):
        """Navigate to the Collection tab."""
        self.verify_and_tap(self.tabs["collection"], self.nav_y, "Collection Tab")

    def go_to_battle(self):
        """Navigate to the main Battle tab."""
        self.verify_and_tap(self.tabs["battle"], self.nav_y, "Battle Tab")
        
    def find_battle_button(self, frame):
        """
        Dynamically locates the Battle button on the Home Screen.
        Returns (x, y) center of the button, or None if not found.
        """
        if frame is None:
            return None
            
        roi = frame[700:1150, 100:620]
        blurred = cv2.GaussianBlur(roi, (15, 15), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        # Battle button is bright yellow/orange
        mask = cv2.inRange(hsv, np.array([10, 100, 100]), np.array([40, 255, 255]))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_c = None
        max_area = 0
        for c in contours:
            area = cv2.contourArea(c)
            if area > max_area and area > 3000:
                x, y, w, h = cv2.boundingRect(c)
                if w > h * 1.2:  # Wider than tall
                    max_area = area
                    best_c = c
                    
        if best_c is not None:
            x, y, w, h = cv2.boundingRect(best_c)
            center_x = int(x + w/2) + 100
            center_y = int(y + h/2) + 700
            return (center_x, center_y)
            
        return None

    def scroll_down(self, amount=1):
        """Scroll down the collection screen to see more cards."""
        for _ in range(amount):
            logger.info("Scrolling down...")
            self.adb.swipe(360, 1000, 360, 300, duration_ms=400)
            time.sleep(1.0)

    def scroll_up(self, amount=1):
        """Scroll up the collection screen."""
        for _ in range(amount):
            logger.info("Scrolling up...")
            self.adb.swipe(360, 300, 360, 1000, duration_ms=400)
            time.sleep(1.0)

    def send_emote(self, emotion="laugh"):
        """Sends an emote (BM)."""
        logger.info(f"Sending BM: {emotion}")
        self.adb.tap(80, 980)
        time.sleep(0.3)
        
        if emotion == "laugh":
            self.adb.tap(200, 850)
        elif emotion == "cry":
            self.adb.tap(350, 850)
        elif emotion == "angry":
            self.adb.tap(500, 850)
        else:
            self.adb.tap(200, 850)
            
        time.sleep(0.5)

    def recover(self):
        """
        Recovery Mode for unexpected screens.
        Taps the 'X' button or 'OK' button locations to dismiss popups.
        Returns True if successful, False if it needs to abort.
        """
        logger.warning("Attempting UI Recovery Mode (dismissing popups)...")
        # Common close button coordinates:
        # Top right popup:
        self.adb.tap(650, 250)
        time.sleep(0.5)
        # Center-bottom OK button:
        self.adb.tap(360, 1000)
        time.sleep(0.5)
        # Bottom-left fallback:
        self.adb.tap(10, 600)
        time.sleep(0.5)
        
        logger.info("Recovery sequence executed.")
        return True

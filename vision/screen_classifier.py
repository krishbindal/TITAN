import cv2
import numpy as np
from enum import Enum


class ScreenState(Enum):

    GAMEPLAY = "gameplay"
    HOME_SCREEN = "home_screen"
    LOADING = "loading"
    VICTORY = "victory"
    DEFEAT = "defeat"
    UNKNOWN = "unknown"


class ScreenClassifier:

    # A non-gameplay state must persist for this many consecutive
    # frames before we actually switch away from GAMEPLAY.
    # This prevents spell effects (Fireball flash, Zap, etc.)
    # from being misclassified as defeat/victory screens.
    # Reduced to 3 because at 1 FPS, 20 frames takes 20 seconds!
    CONFIRM_FRAMES = 3

    def __init__(self):
        self.width = 720
        self.height = 1280

        # State persistence tracking
        self._current_state = ScreenState.UNKNOWN
        self._pending_state = None
        self._pending_count = 0

    def classify(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        raw_state = self._raw_classify(hsv)

        # If we are currently in GAMEPLAY and the raw classifier
        # says something else, require it to persist before switching.
        if self._current_state == ScreenState.GAMEPLAY:
            if raw_state == ScreenState.GAMEPLAY:
                # Still gameplay — reset any pending transition
                self._pending_state = None
                self._pending_count = 0
            else:
                # Non-gameplay detected — start or continue counting
                if raw_state == self._pending_state:
                    self._pending_count += 1
                else:
                    self._pending_state = raw_state
                    self._pending_count = 1

                # Only switch if we've seen it for enough consecutive frames
                if self._pending_count >= self.CONFIRM_FRAMES:
                    self._current_state = raw_state
                    self._pending_state = None
                    self._pending_count = 0
                else:
                    # Not confirmed yet — stay in GAMEPLAY
                    return ScreenState.GAMEPLAY
        else:
            # We are NOT in gameplay. Switch back to gameplay immediately
            # the moment raw says gameplay (no delay needed to resume playing).
            if raw_state == ScreenState.GAMEPLAY:
                self._current_state = ScreenState.GAMEPLAY
                self._pending_state = None
                self._pending_count = 0
            else:
                self._current_state = raw_state

        return self._current_state

    def _raw_classify(self, hsv):
        """Pure color-based classification without persistence logic."""
        if self._is_loading(hsv):
            return ScreenState.LOADING

        # Gameplay is the most distinctive (pink elixir bar) - check this FIRST!
        if self._is_gameplay_explicit(hsv):
            return ScreenState.GAMEPLAY

        if self._is_victory(hsv):
            return ScreenState.VICTORY

        if self._is_defeat(hsv):
            return ScreenState.DEFEAT

        if self._is_home_screen(hsv):
            return ScreenState.HOME_SCREEN
            
        return ScreenState.UNKNOWN

    def is_gameplay(self, frame):
        return self.classify(frame) == ScreenState.GAMEPLAY
        
    def _is_gameplay_explicit(self, hsv):
        # Gameplay always has the bright pink elixir bar at the very bottom
        # Expanded ROI to account for different emulator aspect ratios/bars
        roi = hsv[1150:1280, 100:620]
        # Pink/Magenta color range in OpenCV HSV (matches reader.py)
        pink_ratio = self._color_ratio(roi, [135, 100, 150], [170, 255, 255])
        return pink_ratio > 0.01

    def _color_ratio(self, hsv_roi, lower, upper):
        mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
        if mask.size == 0:
            return 0.0
        return mask.sum() / 255 / mask.size

    def _is_victory(self, hsv):
        # Victory screen: bright blue "WINNER" text and banners in the player's half (center-bottom)
        roi = hsv[400:800, 100:620]
        blue_ratio = self._color_ratio(roi, [100, 150, 150], [130, 255, 255])
        return blue_ratio > 0.20

    def _is_defeat(self, hsv):
        # Defeat screen: bright red text and banners in the player's half
        roi = hsv[400:800, 100:620]
        red_low = self._color_ratio(roi, [0, 150, 150], [10, 255, 255])
        red_high = self._color_ratio(roi, [170, 150, 150], [180, 255, 255])
        return (red_low + red_high) > 0.20

    def _is_loading(self, hsv):
        # Loading screen: very dark overall
        roi = hsv[100:1100, 50:670]
        dark_ratio = self._color_ratio(roi, [0, 0, 0], [180, 255, 60])
        return dark_ratio > 0.85

    def _is_home_screen(self, hsv):
        # Home screen: distinctive orange/gold UI buttons in bottom half (Battle button)
        roi = hsv[640:1100, 100:620]
        orange_ratio = self._color_ratio(roi, [10, 150, 150], [30, 255, 255])
        
        # Also check for the bottom navigation bar (dark blue/grey with bright blue selected tab)
        # Nav bar is at Y=1160-1280
        nav_roi = hsv[1180:1260, 50:670]
        blue_bg_ratio = self._color_ratio(nav_roi, [100, 100, 50], [130, 255, 255])
        
        return orange_ratio > 0.05 or blue_bg_ratio > 0.02

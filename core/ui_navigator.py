import time

class UINavigator:
    """
    Handles navigation between non-gameplay menus in Clash Royale.
    Uses ADB to tap absolute coordinates on a 720x1280 screen layout.
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

    def go_to_collection(self):
        """Navigate to the Collection tab."""
        self.adb.tap(self.tabs["collection"], self.nav_y)
        time.sleep(1.0) # Wait for animation

    def go_to_battle(self):
        """Navigate to the main Battle tab."""
        self.adb.tap(self.tabs["battle"], self.nav_y)
        time.sleep(1.0)

    def scroll_down(self, amount=1):
        """Scroll down the collection screen to see more cards."""
        for _ in range(amount):
            # Swipe from bottom (y=1000) to top (y=300)
            self.adb.swipe(360, 1000, 360, 300, duration_ms=400)
            time.sleep(1.0)

    def scroll_up(self, amount=1):
        """Scroll up the collection screen."""
        for _ in range(amount):
            # Swipe from top (y=300) to bottom (y=1000)
            self.adb.swipe(360, 300, 360, 1000, duration_ms=400)
            time.sleep(1.0)

    def send_emote(self, emotion="laugh"):
        """
        Sends an emote (BM).
        The emote button is at the bottom left above the cards (approx X=80, Y=980).
        After clicking, emotes pop up.
        """
        # 1. Tap Emote Button
        self.adb.tap(80, 980)
        time.sleep(0.3)
        
        # 2. Tap specific emote based on emotion
        if emotion == "laugh":
            # King Laughing (Usually slot 1 or 2)
            self.adb.tap(200, 850)
        elif emotion == "cry":
            # King Crying (Usually slot 3 or 4)
            self.adb.tap(350, 850)
        elif emotion == "angry":
            self.adb.tap(500, 850)
        else:
            # Default first slot
            self.adb.tap(200, 850)
            
        time.sleep(0.5)


import time

class UpgradeManager:
    """
    Manages the autonomous upgrading of cards in the Clash Royale collection.
    """
    def __init__(self, adb_controller, ui_navigator, collection_reader):
        self.adb = adb_controller
        self.nav = ui_navigator
        self.reader = collection_reader

    def execute_upgrade_sweep(self):
        """
        Sweeps the collection tab for upgradable cards and upgrades them if affordable.
        Assumes the bot is already on the Collection Tab.
        """
        print("[TITAN] Initiating Card Upgrade Sweep...")
        
        # Scroll back to the very top to start fresh
        self.nav.scroll_up(amount=5)
        
        for scroll_step in range(4): # Scroll 4 times to check the main chunks of the collection
            # Capture the screen
            frame = self.adb.capture_screen()
            
            # Find green upgrade bars
            upgradable_coords = self.reader.find_upgradable_cards(frame)
            
            # Read our total gold
            current_gold = self.reader.read_top_right_gold(frame)
            print(f"[TITAN] Current Bank: {current_gold} Gold. Found {len(upgradable_coords)} upgradable cards here.")
            
            for (cx, cy) in upgradable_coords:
                print(f"[TITAN] Tapping upgradable card at ({cx}, {cy})")
                self.adb.tap(cx, cy)
                time.sleep(1.0) # Wait for info popup
                
                # Tap the "Upgrade" button on the info panel (Approximate center-bottom)
                self.adb.tap(360, 950)
                time.sleep(1.0) # Wait for gold confirmation popup
                
                # Capture screen again to read the cost
                popup_frame = self.adb.capture_screen()
                cost = self.reader.read_upgrade_cost(popup_frame)
                print(f"[TITAN] Upgrade requires: {cost} Gold.")
                
                if current_gold >= cost and cost > 0:
                    print(f"[TITAN] Sufficient gold! Purchasing upgrade...")
                    # Tap the final gold cost button to confirm
                    self.adb.tap(360, 850)
                    time.sleep(3.0) # Wait for the long upgrade animation
                    
                    # Update our internal bank
                    current_gold -= cost
                    
                    # Tap to skip the rest of the animation
                    self.adb.tap(100, 100)
                    time.sleep(1.0)
                else:
                    print(f"[TITAN] Insufficient gold. Cancelling.")
                    # Tap outside the popup to close it
                    self.adb.tap(100, 100)
                    time.sleep(1.0)
                    # Tap outside the info panel to close it
                    self.adb.tap(100, 100)
                    time.sleep(1.0)

            # Scroll down to reveal more cards
            self.nav.scroll_down(amount=1)
            time.sleep(1.0)
            
        print("[TITAN] Upgrade Sweep Complete.")

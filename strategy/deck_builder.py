import random
import time
import os
import pickle
import logging
from strategy.deck_optimizer import DeckOptimizer

logger = logging.getLogger("TITAN")

class DeckBuilder:
    """
    Intelligent Reinforcement Learning Deck Builder.
    Suggests decks based on historical win rates using an RL optimizer.
    """
    def __init__(self, adb_controller, ui_navigator, collection_reader=None):
        self.adb = adb_controller
        self.nav = ui_navigator
        self.reader = collection_reader
        self.optimizer = DeckOptimizer()

        
        # Grid coordinates for the 8 active deck slots (720x1280)
        self.deck_slots = [
            (150, 250), (290, 250), (430, 250), (570, 250), # Row 1
            (150, 450), (290, 450), (430, 450), (570, 450)  # Row 2
        ]
        
        # Grid X coordinates for the collection columns
        self.collection_cols = [150, 290, 430, 570]
        self.collection_rows = [650, 850, 1050]
        
        self.current_deck = []
        
    def record_match_result(self, won: bool):
        """Called by the main loop after a match to record if the deck worked."""
        if self.current_deck:
            self.optimizer.record_match(self.current_deck, won)
            logger.info(f"Recorded match result for deck. Won: {won}")


    def hit_and_try_mutate(self):
        """
        If the last deck lost, mutate it by swapping 1 to 3 random cards from the collection.
        """
        # Scroll up to ensure we are at the top of the collection tab
        self.nav.scroll_up(amount=3)
        time.sleep(1.0)
        
        # Determine how many cards to swap (1 to 3)
        num_swaps = random.randint(1, 3)
        logger.info(f"Mutating deck... Swapping {num_swaps} cards.")
        
        for _ in range(num_swaps):
            # Scroll down randomly to pick a card from deeper in the collection
            scrolls = random.randint(0, 3)
            if scrolls > 0:
                self.nav.scroll_down(amount=scrolls)
                time.sleep(1.0)
                
            # Pick a random card from the visible collection
            src_x = random.choice(self.collection_cols)
            src_y = random.choice(self.collection_rows)
            
            # Pick a random active deck slot to replace
            dst_x, dst_y = random.choice(self.deck_slots)
            
            logger.info(f"Dragging card from ({src_x}, {src_y}) to deck slot ({dst_x}, {dst_y})")
            # In Clash Royale, to swap a card:
            # Tap the collection card (src), wait for the "Use" menu
            self.adb.tap(src_x, src_y)
            time.sleep(1.0)
            
            # Tap "Use" button on the popup (approx x=200, y=900)
            self.adb.tap(200, 900)
            time.sleep(1.0)
            
            # Tap the destination deck slot
            self.adb.tap(dst_x, dst_y)
            time.sleep(1.0)
            
        # Generate a new random ID for this combination
        self.current_deck_id = f"deck_{random.randint(1000, 9999)}"
        logger.info(f"Mutation complete. Testing new configuration: {self.current_deck_id}")

    def _verify_popup(self, original_frame):
        """
        Waits for a popup to open by checking if the background dims significantly.
        Returns the popup_frame if successful, None if it failed.
        """
        bg_grid = original_frame[100:200, 50:150]
        original_mean = bg_grid.mean()
        
        for attempt in range(4):
            time.sleep(0.5)
            popup_frame = self.adb.capture_screen()
            if popup_frame is None:
                continue
                
            bg_popup = popup_frame[100:200, 50:150]
            current_mean = bg_popup.mean()
            
            if current_mean < original_mean - 5.0:
                # Background dimmed significantly, popup is open!
                return popup_frame
                
        return None

    def build_specific_deck(self, target_deck_list):
        """
        Intelligently builds a specific deck by scanning the collection and using OCR.
        - Skips locked cards (greyed out in the grid)
        - Swipes to the info slide to read detailed stats
        - Stores all scanned card data for upgrade suggestions
        
        target_deck_list is a list of 8 card names (e.g. ['giant', 'musketeer', ...])
        """
        logger.info(f"Intelligent Deck Builder Activated.")
        logger.info(f"Target Deck: {target_deck_list}")
        
        if not self.reader:
            logger.error("CollectionReader missing, aborting intelligent build.")
            return

        # Store all scanned card info for upgrade suggestions
        self.scanned_cards = []

        # Ensure we are at the top of the collection
        self.nav.scroll_up(amount=5)
        time.sleep(1.0)
        
        cards_found = 0
        cards_needed = list(target_deck_list)
        
        # We will scan down the collection a maximum of 10 scrolls
        for scroll in range(10):
            if len(cards_needed) == 0:
                logger.info("Deck successfully built!")
                break
                
            logger.info(f"Scanning collection (Scroll {scroll}/10)...")
            
            # Capture screen once for locked-card checks on this page
            grid_frame = self.adb.capture_screen()
            if grid_frame is None:
                continue
            
            # Tap each visible card
            for r in self.collection_rows:
                for c in self.collection_cols:
                    if len(cards_needed) == 0:
                        break
                    
                    # --- Check if card is locked BEFORE tapping ---
                    if self.reader.is_card_locked(grid_frame, c, r):
                        logger.info(f"Card at ({c}, {r}) is LOCKED. Skipping.")
                        continue
                        
                    # Abort if we are no longer on the home screen (e.g., user started a match)
                    import cv2
                    import numpy as np
                    hsv = cv2.cvtColor(grid_frame, cv2.COLOR_BGR2HSV)
                    nav_roi = hsv[1180:1260, 50:670]
                    blue_mask = cv2.inRange(nav_roi, np.array([100, 100, 50]), np.array([130, 255, 255]))
                    if nav_roi.size == 0 or (cv2.countNonZero(blue_mask) / (nav_roi.shape[0] * nav_roi.shape[1])) < 0.02:
                        logger.warning("Aborting deck build! Screen is no longer Home Screen.")
                        return
                        
                    # Tap to open popup
                    self.adb.tap(c, r)
                    
                    popup_frame = self._verify_popup(grid_frame)
                    if popup_frame is None:
                        logger.warning(f"No popup detected at ({c}, {r}). Assuming tap failed or lag. Skipping.")
                        self.adb.tap(10, 600) # Fallback close
                        time.sleep(0.5)
                        continue
                    
                    card_name = self.reader.read_card_popup_name(popup_frame, c, r)
                    card_level = self.reader.read_card_level(popup_frame)
                    logger.info(f"OCR read: '{card_name}' (Level {card_level})")
                    
                    # --- Swipe LEFT to info slide to read stats ---
                    self.adb.swipe(380, 430, 80, 430, duration_ms=300)
                    time.sleep(1.0)
                    
                    stats_frame = self.adb.capture_screen()
                    card_stats = {}
                    if stats_frame is not None:
                        card_stats = self.reader.read_card_info_slide(stats_frame)
                        stat_summary = {k: v for k, v in card_stats.items() if k != "raw"}
                        logger.info(f"Stats: {stat_summary if stat_summary else card_stats.get('raw', 'N/A')}")
                    
                    # Store scanned card data
                    self.scanned_cards.append({
                        "name": card_name,
                        "level": card_level,
                        "stats": card_stats,
                        "grid_pos": (c, r),
                    })
                    
                    # --- Check if this card matches one we need ---
                    import difflib
                    matched_card = None
                    clean_name = card_name.replace('\n', ' ').replace('levels', '').replace('level', '').replace('a', '').strip()
                    
                    for target in cards_needed:
                        # Direct match
                        if target in clean_name or clean_name in target:
                            matched_card = target
                            break
                        
                        # Fuzzy match
                        words = clean_name.split()
                        for w in words:
                            if len(w) > 3 and difflib.SequenceMatcher(None, target, w).ratio() > 0.65:
                                matched_card = target
                                break
                        
                        # Full string fuzzy match just in case
                        if not matched_card and difflib.SequenceMatcher(None, target, clean_name).ratio() > 0.6:
                            matched_card = target
                            
                        if matched_card:
                            break
                    
                    if matched_card:
                        logger.info(f"*** Found target card: {matched_card}! ***")
                        
                        # Swipe back to main view first (swipe right)
                        self.adb.swipe(80, 430, 380, 430, duration_ms=300)
                        time.sleep(0.5)
                        
                        # Tap 'Use' button (approx center-bottom of popup)
                        self.adb.tap(200, 900)
                        time.sleep(1.0)
                        
                        # Tap the corresponding deck slot
                        slot_idx = target_deck_list.index(matched_card)
                        slot_x, slot_y = self.deck_slots[slot_idx]
                        self.adb.tap(slot_x, slot_y)
                        time.sleep(1.0)
                        
                        cards_needed.remove(matched_card)
                        cards_found += 1
                    else:
                        # Not a target card — close popup via X button (top-right)
                        self.adb.tap(650, 280)
                        time.sleep(0.5)
                        
            if len(cards_needed) > 0:
                self.nav.scroll_down(amount=1)
                time.sleep(1.0)
                # Re-capture grid for locked checks on new page
                grid_frame = self.adb.capture_screen()
                
        if len(cards_needed) > 0:
            logger.info(f"Finished scanning. Missing cards: {cards_needed}")
        
        # --- Print Upgrade Suggestions ---
        self._print_upgrade_suggestions()
            
        # Update current deck ID for the RL tracker
        self.current_deck_id = "meta_deck_1"

    def scan_entire_collection(self):
        """
        Scans all unlocked cards in the collection, reading their stats.
        Stores them in self.scanned_cards.
        """
        logger.info("Initiating Full Collection Scan...")
        self.scanned_cards = []
        self.nav.scroll_up(amount=5)
        time.sleep(1.0)
        
        # Set to track cards we've already processed (to avoid duplicates from scrolling)
        processed_cards = set()
        
        for scroll in range(10):
            logger.info(f"Scanning page (Scroll {scroll}/10)...")
            grid_frame = self.adb.capture_screen()
            if grid_frame is None:
                continue
                
            page_found_new = False
            for r in self.collection_rows:
                for c in self.collection_cols:
                    if self.reader.is_card_locked(grid_frame, c, r):
                        continue
                        
                    # Abort if we are no longer on the home screen (e.g., user started a match)
                    import cv2
                    import numpy as np
                    hsv = cv2.cvtColor(grid_frame, cv2.COLOR_BGR2HSV)
                    nav_roi = hsv[1180:1260, 50:670]
                    blue_mask = cv2.inRange(nav_roi, np.array([100, 100, 50]), np.array([130, 255, 255]))
                    if nav_roi.size == 0 or (cv2.countNonZero(blue_mask) / (nav_roi.shape[0] * nav_roi.shape[1])) < 0.02:
                        logger.warning("Aborting scan! Screen is no longer Home Screen (Did you start a match?)")
                        return None
                        
                    self.adb.tap(c, r)
                    
                    popup_frame = self._verify_popup(grid_frame)
                    if popup_frame is None:
                        logger.warning(f"No popup detected at ({c}, {r}). Skipping.")
                        self.adb.tap(10, 600)
                        time.sleep(0.5)
                        continue
                        
                    card_name = self.reader.read_card_popup_name(popup_frame, c, r)
                    card_level = self.reader.read_card_level(popup_frame)
                    
                    # Prevent rescanning
                    if card_name in processed_cards:
                        self.adb.tap(650, 280) # Close popup via X button
                        time.sleep(0.5)
                        continue
                        
                    processed_cards.add(card_name)
                    page_found_new = True
                    logger.info(f"Discovered: '{card_name}' (Level {card_level})")
                    
                    # Swipe to stats
                    self.adb.swipe(380, 430, 80, 430, duration_ms=300)
                    time.sleep(1.0)
                    
                    stats_frame = self.adb.capture_screen()
                    card_stats = {}
                    if stats_frame is not None:
                        card_stats = self.reader.read_card_info_slide(stats_frame)
                        
                    self.scanned_cards.append({
                        "name": card_name,
                        "level": card_level,
                        "stats": card_stats,
                        "grid_pos": (c, r)
                    })
                    
                    # Close popup via X button
                    self.adb.tap(650, 280)
                    time.sleep(0.5)
                    
            if not page_found_new and scroll > 2:
                # If we've scrolled down and didn't find any new cards, we likely hit the end or just locked cards
                logger.info("No new unlocked cards found on this page. Scan complete.")
                break
                
            self.nav.scroll_down(amount=1)
            time.sleep(1.0)
            
        logger.info(f"Collection Scan Finished. Indexed {len(self.scanned_cards)} unlocked cards.")

    def generate_optimal_deck(self):
        """
        Uses heuristics on self.scanned_cards stats to select 8 cards.
        """
        if len(self.scanned_cards) < 8:
            logger.warning("Found fewer than 8 unlocked cards. Falling back to basics.")
            # We must return exactly 8 cards. If we don't have enough, we're in trouble.
            # In a real game, you always have 8+ cards after the tutorial.
            return ["arrows", "bomber", "archers", "knight", "fireball", "mini_pekka", "musketeer", "giant"]
            
        logger.info("Analyzing card stats to build optimal strategy...")
        
        # Categorize cards heuristically
        tanks = []
        ranged = []
        spells = []
        others = []
        
        for card in self.scanned_cards:
            stats = card.get("stats", {})
            hp = stats.get("hp", 0)
            dmg = stats.get("damage", 0)
            rng = stats.get("range", 0)
            radius = stats.get("radius", 0)
            
            # Simple heuristic
            if hp > 1000 or (hp > 500 and rng == 0):
                tanks.append(card)
            elif radius > 0 and hp == 0: # Spells usually don't list HP, but have radius/area damage
                spells.append(card)
            elif rng > 2.0:
                ranged.append(card)
            else:
                others.append(card)
                
        # Sort each pool by perceived 'power' (level * dmg * hp if available)
        def score_card(c):
            lvl = max(1, c.get("level", 1))
            st = c.get("stats", {})
            return lvl * (st.get("hp", 100) + st.get("damage", 10))
            
        tanks = sorted(tanks, key=score_card, reverse=True)
        ranged = sorted(ranged, key=score_card, reverse=True)
        spells = sorted(spells, key=score_card, reverse=True)
        others = sorted(others, key=score_card, reverse=True)
        
        # Select components
        selected = []
        
        # 2 Tanks/Melee bruisers
        for c in tanks[:2]:
            selected.append(c["name"])
            tanks.remove(c)
            
        # 2 Ranged/Anti-air
        for c in ranged[:2]:
            selected.append(c["name"])
            ranged.remove(c)
            
        # 1-2 Spells
        for c in spells[:2]:
            selected.append(c["name"])
            spells.remove(c)
            
        # Fill the rest (up to 8) from highest scoring remaining cards
        remaining_pool = tanks + ranged + spells + others
        remaining_pool = sorted(remaining_pool, key=score_card, reverse=True)
        
        while len(selected) < 8 and remaining_pool:
            c = remaining_pool.pop(0)
            if c["name"] not in selected:
                selected.append(c["name"])
                
        # Fallback deduplication just in case
        selected = list(set(selected))
        if len(selected) < 8:
            logger.warning("Deck generation failed to get 8 unique cards. Using fallback.")
            core_deck = ["giant", "musketeer", "arrows", "knight", "minions", "goblin_cage", "fireball", "mini_pekka"]
        else:
            core_deck = selected
            
        # 2. Let the Deck Optimizer choose whether to exploit the best historical deck or explore by mutating
        available_card_names = [c["name"] for c in self.scanned_cards]
        optimal_deck = self.optimizer.suggest_deck(available_card_names, core_deck, epsilon=0.2)
        
        logger.info(f"Generated Optimal Deck: {optimal_deck}")
        self.current_deck = optimal_deck
        return optimal_deck

    def auto_build_deck(self):
        """
        Complete loop: Scan, Generate, Build.
        """
        logger.info("="*50)
        logger.info("AUTONOMOUS DECK ASSEMBLY INITIATED")
        logger.info("="*50)
        self.scan_entire_collection()
        target_deck = self.generate_optimal_deck()
        self.build_specific_deck(target_deck)
        logger.info("Autonomous Deck Assembly Complete.")

    def _print_upgrade_suggestions(self):
        """Analyze scanned cards and suggest which to upgrade."""
        if not self.scanned_cards:
            return
            
        logger.info(f"\n{'='*50}")
        logger.info(f"UPGRADE SUGGESTIONS (scanned {len(self.scanned_cards)} cards)")
        logger.info(f"{'='*50}")
        
        # Sort by level (lowest first — those benefit most from upgrading)
        by_level = sorted(self.scanned_cards, key=lambda c: c.get("level", 0))
        
        # Show highest-level cards (these are your strongest, keep upgrading them)
        high_level = [c for c in by_level if c.get("level", 0) >= 3]
        low_level = [c for c in by_level if 0 < c.get("level", 0) < 3]
        
        if high_level:
            logger.info(">> Your strongest cards (keep upgrading):")
            for card in high_level[-5:]:
                name = card['name'].replace('_', ' ').title()
                dmg = card['stats'].get('damage', '?')
                hp = card['stats'].get('hp', '?')
                logger.info(f"   Lv.{card['level']} {name} | Damage: {dmg} | HP: {hp}")
        
        if low_level:
            logger.info(">> Low-level cards (consider upgrading if in your deck):")
            for card in low_level[:5]:
                name = card['name'].replace('_', ' ').title()
                logger.info(f"   Lv.{card['level']} {name}")
        
        logger.info(f"{'='*50}\n")


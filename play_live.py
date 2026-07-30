"""
Live Gameplay Script for TITAN.
Connects to BlueStacks via ADB, reads the screen in real-time,
and injects swipes to play cards autonomously.

Features resilient error handling with auto-reconnect.
"""

import time
import traceback
import argparse
import copy

from core.adb_controller import ADBController
from engine.async_engine import AsyncEngine
from configs.settings import MODEL_PATH
from vision.visualizer import Visualizer
from dashboard.app import start_dashboard

from core.ui_navigator import UINavigator
from vision.collection_reader import CollectionReader
from strategy.deck_builder import DeckBuilder
from core.analytics import get_engine, MatchLogger, ReplayLogger

# Global state for dashboard
_latest_frame = None
_latest_telemetry = {
    "status": "waiting",
    "fps": 0,
    "strategy_mode": "standard",
    "action": "WAIT",
    "suggestion": "Booting up strategy module...",
    "elixir_advantage": 0.0,
    "hot_lane": "balanced",
    "pressure": False,
}


def get_dashboard_frame():
    return _latest_frame


def get_dashboard_telemetry():
    return _latest_telemetry


def main():
    parser = argparse.ArgumentParser(description="TITAN S-CLASS Live Agent")
    parser.add_argument(
        "--dashboard", action="store_true", help="Launch the Web Dashboard"
    )
    args = parser.parse_args()

    if args.dashboard:
        print("=" * 50)
        print(" Starting TITAN Dashboard Server...")
        start_dashboard(get_dashboard_frame, get_dashboard_telemetry)

    print("=" * 50)
    print(" TITAN S-CLASS: LIVE AUTONOMOUS MODE")
    print("=" * 50)

    print("Initializing ADB Controller...")
    adb = ADBController("127.0.0.1:5555")

    print("Loading AI Models (Async)...", flush=True)
    pipeline = AsyncEngine(MODEL_PATH, process_every_n=4)
    pipeline.start()
    visualizer = Visualizer()

    print("Initializing Management Modules...", flush=True)
    navigator = UINavigator(adb)
    collection_reader = CollectionReader()
    deck_builder = DeckBuilder(adb, navigator, collection_reader)

    print("System Ready. Monitoring live feed...", flush=True)

    frame_count = 0
    consecutive_failures = 0
    max_consecutive_failures = 30
    
    was_in_gameplay = False
    needs_management = True
    last_match_won = False
    
    match_logger = None
    replay_logger = None

    while True:
        try:
            # 1. Capture screen
            start_time = time.time()
            # print("DEBUG: Capturing screen...", flush=True)
            frame = adb.capture_screen()
            # print("DEBUG: Screen captured.", flush=True)

            if frame is None:
                consecutive_failures += 1

                if consecutive_failures >= max_consecutive_failures:
                    print(
                        "\n[TITAN] Too many capture failures. Attempting reconnect...", flush=True
                    )
                    if adb.reconnect():
                        consecutive_failures = 0
                        continue
                    else:
                        print("[TITAN] Could not reconnect. Waiting 10s...", flush=True)
                        time.sleep(10)
                        consecutive_failures = 0
                        continue

                time.sleep(0.1)
                continue

            consecutive_failures = 0

            # 2. Process frame through TITAN AI (Async)
            # print("DEBUG: Submitting frame...", flush=True)
            game_state, action, screen_state, suggestion = pipeline.submit_frame(frame)
            
            if screen_state is None:
                # Async engine hasn't finished its first inference yet.
                time.sleep(0.01)
                continue
                
            # print(f"DEBUG: Frame processed. Screen State: {screen_state.name}", flush=True)

            # 2.5 Update Visuals & Telemetry
            global _latest_frame, _latest_telemetry

            # Get detections (safe to read from pipeline's tracker)
            detections = (
                pipeline.pipeline.tracker.get_confirmed_tracks()
                if screen_state.name == "GAMEPLAY"
                else []
            )

            # Update telemetry
            elapsed = time.time() - start_time
            fps = 1.0 / elapsed if elapsed > 0 else 0

            action_name = "WAIT"
            if action:
                if action.action.name == "PLAY_CARD":
                    action_name = f"PLAY {action.card_to_play.upper()}"
                else:
                    action_name = action.action.name

            if game_state and hasattr(pipeline, "pipeline"):
                # Access strategy through the inner pipeline object in AsyncEngine
                threat_report = pipeline.pipeline.strategy.get_threat_report(game_state)
                elixir_adv = pipeline.pipeline.strategy.elixir.get_elixir_advantage()
                
                # Fetch memory stats for overlay
                memory = pipeline.pipeline.strategy.memory
                predicted_deck = list(memory.deck)
                enemy_elixir = memory.enemy_elixir
                
                # Get the last scores from the logger if available, otherwise empty
                # We can just put some basic stats in telemetry to pass to visualizer
                
                _latest_telemetry = {
                    "status": "active",
                    "fps": fps,
                    "strategy_mode": pipeline.pipeline.strategy._mode.__name__.split(".")[-1],
                    "action": action_name,
                    "suggestion": suggestion or "",
                    "elixir_advantage": elixir_adv,
                    "enemy_elixir": enemy_elixir,
                    "predicted_deck": predicted_deck,
                    "hot_lane": threat_report.hot_lane,
                    "pressure": threat_report.pressure,
                }
            else:
                _latest_telemetry["status"] = "active"
                _latest_telemetry["fps"] = fps
                _latest_telemetry["action"] = screen_state.name
                _latest_telemetry["suggestion"] = f"Screen: {screen_state.name}"
                _latest_telemetry["elixir_advantage"] = 0.0
                _latest_telemetry["enemy_elixir"] = 0.0
                _latest_telemetry["predicted_deck"] = []
                _latest_telemetry["hot_lane"] = "balanced"
                _latest_telemetry["pressure"] = False

            _latest_frame = visualizer.draw(frame, detections, action, telemetry=_latest_telemetry)
            
            if replay_logger:
                replay_logger.log_frame(_latest_frame)

            # 3. Handle Game States (Management vs Gameplay)
            if screen_state.name == "GAMEPLAY":
                if not was_in_gameplay:
                    session_id = pipeline.pipeline.strategy.session_id if hasattr(pipeline.pipeline, 'strategy') else int(time.time())
                    match_logger = MatchLogger(get_engine(), session_id)
                    match_logger.start_match()
                    replay_logger = ReplayLogger(session_id)
                was_in_gameplay = True
            elif screen_state.name == "VICTORY":
                if was_in_gameplay:
                    print("\n[TITAN] VICTORY DETECTED! BMing opponent...")
                    navigator.send_emote("laugh")
                    deck_builder.record_match_result(won=True)
                    if match_logger:
                        match_logger.end_match(won=True)
                        match_logger = None
                    if replay_logger:
                        replay_logger.stop()
                        replay_logger = None
                    # Train RL
                    if pipeline.pipeline.strategy._mode.__name__.endswith("rl"):
                        pipeline.pipeline.strategy._mode.apply_match_result(won=True)
                    was_in_gameplay = False
                    needs_management = True
                    last_match_won = True
            elif screen_state.name == "DEFEAT":
                if was_in_gameplay:
                    print("\n[TITAN] DEFEAT DETECTED. Sending sad emote...")
                    navigator.send_emote("cry")
                    deck_builder.record_match_result(won=False)
                    if match_logger:
                        match_logger.end_match(won=False)
                        match_logger = None
                    if replay_logger:
                        replay_logger.stop()
                        replay_logger = None
                    # Train RL
                    if pipeline.pipeline.strategy._mode.__name__.endswith("rl"):
                        pipeline.pipeline.strategy._mode.apply_match_result(won=False)
                    was_in_gameplay = False
                    needs_management = True
                    last_match_won = False
            elif screen_state.name == "HOME_SCREEN":
                if needs_management:
                    print("\n[TITAN] Running post-match management tasks...")
                    # 1. Go to collection
                    navigator.go_to_collection()
                    time.sleep(2.0)
                    
                    # 2. Scan card stats and suggest upgrades (NO auto-upgrading)
                    scan_frame = adb.capture_screen()
                    if scan_frame is not None:
                        upgradable = collection_reader.find_upgradable_cards(scan_frame)
                        gold = collection_reader.read_top_right_gold(scan_frame)
                        if upgradable:
                            print(f"[TITAN] UPGRADE SUGGESTIONS: Found {len(upgradable)} cards ready to upgrade. Gold: {gold}")
                            print(f"[TITAN] Card positions: {upgradable}")
                            print(f"[TITAN] >> User should manually upgrade their highest-level cards.")
                        else:
                            print(f"[TITAN] No cards ready to upgrade. Gold: {gold}")
                    
                    # 3. Rebuild deck if we lost (or on first boot)
                    if last_match_won is False:
                        deck_builder.auto_build_deck()
                        
                    # 4. Start next match
                    print("[TITAN] Starting new match!")
                    navigator.go_to_battle()
                    # Click Battle button (accurate coords for center button)
                    adb.tap(360, 1030)
                    time.sleep(2.0)
                    needs_management = False

            # 4. Execute Actions (During Gameplay)
            if (
                action
                and action.action.name == "PLAY_CARD"
                and game_state
                and game_state.hand
            ):
                if action.card_to_play in game_state.hand:
                    card_idx = game_state.hand.index(action.card_to_play)
                    print(
                        f"\n>>> [TITAN] PLAYING {action.card_to_play.upper()} "
                        f"(slot {card_idx}) at ({action.target_x}, {action.target_y}) | "
                        f"Elixir: {pipeline.pipeline.strategy.elixir.player_elixir:.1f}"
                    )
                    adb.play_card(card_idx, action.target_x, action.target_y)
                    
                    if match_logger:
                        match_logger.record_action()
                        
                    # Deduct elixir cost from tracker
                    pipeline.pipeline.strategy.elixir.deduct_card_play(action.card_to_play)

            # 5. Diagnostics
            if frame_count % 10 == 0:
                hand = game_state.hand if game_state else []
                state_name = screen_state.name if screen_state else "N/A"
                elx = pipeline.pipeline.strategy.elixir.player_elixir if hasattr(pipeline.pipeline.strategy, 'elixir') else '?'
                print(f"Status: {state_name} | FPS: {fps:.1f} | Elixir: {elx} | Hand: {hand}")

            frame_count += 1

        except KeyboardInterrupt:
            print("\nTITAN shut down safely by user.")
            break

        except Exception as e:
            print(f"\n[TITAN] Unexpected error: {e}")
            traceback.print_exc()
            print("[TITAN] Recovering in 2 seconds...")
            time.sleep(2)
            
    # Cleanup
    if hasattr(pipeline, "stop"):
        pipeline.stop()


if __name__ == "__main__":
    main()

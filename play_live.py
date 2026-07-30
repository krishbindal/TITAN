"""
Live Gameplay Script for TITAN.
Connects to BlueStacks via ADB, reads the screen in real-time,
and injects swipes to play cards autonomously.

Features an explicit State Machine and dual operating modes (Play / Manage).
"""

import time
import traceback
import argparse
import copy
import logging
import cv2
import numpy as np
from enum import Enum, auto

from core.adb_controller import ADBController
from engine.async_engine import AsyncEngine
from configs.settings import MODEL_PATH
from vision.visualizer import Visualizer
from dashboard.app import start_dashboard

from core.ui_navigator import UINavigator
from vision.collection_reader import CollectionReader
from strategy.deck_builder import DeckBuilder
from core.analytics import get_engine, MatchLogger, ReplayLogger

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("TITAN")
# Reduce noisy loggers
logging.getLogger("werkzeug").setLevel(logging.WARNING)

class AppState(Enum):
    FIRST_BOOT = auto()
    HOME_SCREEN = auto()
    IN_MATCH = auto()
    POST_MATCH_BM = auto()
    RETURNING_HOME = auto()
    RECOVERY = auto()

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

def update_telemetry(frame, screen_state, action, game_state, pipeline, suggestion, fps, visualizer):
    global _latest_frame, _latest_telemetry
    
    detections = (
        pipeline.pipeline.tracker.get_confirmed_tracks()
        if screen_state and screen_state.name == "GAMEPLAY"
        else []
    )

    action_name = "WAIT"
    if action:
        if action.action.name == "PLAY_CARD":
            action_name = f"PLAY {action.card_to_play.upper()}"
        else:
            action_name = action.action.name

    if game_state and hasattr(pipeline, "pipeline"):
        threat_report = pipeline.pipeline.strategy.get_threat_report(game_state)
        elixir_adv = pipeline.pipeline.strategy.elixir.get_elixir_advantage()
        memory = pipeline.pipeline.strategy.memory
        
        _latest_telemetry = {
            "status": "active",
            "fps": fps,
            "strategy_mode": pipeline.pipeline.strategy._mode.__name__.split(".")[-1],
            "action": action_name,
            "suggestion": suggestion or "",
            "elixir_advantage": elixir_adv,
            "enemy_elixir": memory.enemy_elixir,
            "predicted_deck": list(memory.deck),
            "hot_lane": threat_report.hot_lane,
            "pressure": threat_report.pressure,
        }
    else:
        _latest_telemetry["status"] = "active"
        _latest_telemetry["fps"] = fps
        _latest_telemetry["action"] = screen_state.name if screen_state else "UNKNOWN"
        _latest_telemetry["suggestion"] = f"Screen: {screen_state.name if screen_state else 'None'}"
        _latest_telemetry["elixir_advantage"] = 0.0
        _latest_telemetry["enemy_elixir"] = 0.0
        _latest_telemetry["predicted_deck"] = []
        _latest_telemetry["hot_lane"] = "balanced"
        _latest_telemetry["pressure"] = False

    _latest_frame = visualizer.draw(frame, detections, action, telemetry=_latest_telemetry)
    return _latest_frame


def run_play_mode(adb, pipeline, visualizer, navigator, deck_builder):
    """Executes the autonomous playing loop."""
    logger.info("Entering PLAY MODE.")
    state = AppState.FIRST_BOOT
    
    frame_count = 0
    consecutive_failures = 0
    
    match_logger = None
    replay_logger = None
    last_match_won = False
    last_processed_result_id = -1
    
    while True:
        try:
            start_time = time.time()
            frame = adb.capture_screen()
            if frame is None:
                consecutive_failures += 1
                if consecutive_failures >= 30:
                    logger.warning("Too many capture failures. Attempting reconnect...")
                    if adb.reconnect():
                        consecutive_failures = 0
                    else:
                        time.sleep(5)
                time.sleep(0.1)
                continue
            
            consecutive_failures = 0
            
            # Submit to AI
            game_state, action, screen_state, suggestion, result_id = pipeline.submit_frame(frame)
            if screen_state is None:
                time.sleep(0.01)
                continue
                
            elapsed = time.time() - start_time
            fps = 1.0 / elapsed if elapsed > 0 else 0
            
            # Update telemetry and dashboard
            annotated_frame = update_telemetry(frame, screen_state, action, game_state, pipeline, suggestion, fps, visualizer)
            if replay_logger:
                replay_logger.log_frame(annotated_frame)
                
            # State Machine Transitions
            if state == AppState.FIRST_BOOT:
                if screen_state.name == "HOME_SCREEN":
                    logger.info("Boot successful. Home screen detected.")
                    state = AppState.HOME_SCREEN
                elif screen_state.name == "GAMEPLAY":
                    logger.info("Booted directly into gameplay! Resuming match.")
                    state = AppState.IN_MATCH
                elif screen_state.name == "UNKNOWN":
                    # Potentially an offer or popup
                    if navigator.recover():
                        state = AppState.HOME_SCREEN
            
            elif state == AppState.HOME_SCREEN:
                if screen_state.name == "HOME_SCREEN":
                    logger.info("Locating Battle button...")
                    btn = navigator.find_battle_button(frame)
                    if btn:
                        logger.info(f"Battle button found at {btn}. Initiating match!")
                        adb.tap(btn[0], btn[1])
                        time.sleep(2.0)
                    else:
                        logger.warning("Battle button not found. Waiting or attempting recovery.")
                        navigator.recover()
                elif screen_state.name == "MATCHMAKING" or screen_state.name == "GAMEPLAY":
                    state = AppState.IN_MATCH
                    
            elif state == AppState.IN_MATCH:
                if not match_logger:
                    session_id = pipeline.pipeline.strategy.session_id if hasattr(pipeline.pipeline, 'strategy') else int(time.time())
                    match_logger = MatchLogger(get_engine(), session_id)
                    match_logger.start_match()
                    replay_logger = ReplayLogger(session_id)
                    
                if screen_state.name == "GAMEPLAY":
                    # Execute Plays
                    if action and result_id > last_processed_result_id:
                        if action.action.name == "PLAY_CARD" and game_state and game_state.hand:
                            if action.card_to_play in game_state.hand:
                                card_idx = game_state.hand.index(action.card_to_play)
                                elx = pipeline.pipeline.strategy.elixir.player_elixir
                                logger.info(f"PLAYING {action.card_to_play.upper()} (slot {card_idx}) at ({action.target_x}, {action.target_y}) | Elixir: {elx:.1f}")
                                adb.play_card(card_idx, action.target_x, action.target_y)
                                if match_logger:
                                    match_logger.record_action()
                                pipeline.pipeline.strategy.elixir.deduct_card_play(action.card_to_play)
                                
                        # Mark this result as processed regardless of whether it was PLAY_CARD or WAIT
                        last_processed_result_id = result_id
                            
                elif screen_state.name in ["VICTORY", "DEFEAT"]:
                    won = (screen_state.name == "VICTORY")
                    logger.info(f"Match Concluded. Result: {'VICTORY' if won else 'DEFEAT'}")
                    
                    if match_logger:
                        match_logger.end_match(won=won)
                        match_logger = None
                    if replay_logger:
                        replay_logger.stop()
                        replay_logger = None
                        
                    deck_builder.record_match_result(won=won)
                    if hasattr(pipeline.pipeline.strategy, "_mode") and pipeline.pipeline.strategy._mode.__name__.endswith("rl"):
                        pipeline.pipeline.strategy._mode.apply_match_result(won=won)
                        
                    last_match_won = won
                    state = AppState.POST_MATCH_BM
                    
            elif state == AppState.POST_MATCH_BM:
                logger.info("Sending post-match BM...")
                navigator.send_emote("laugh" if last_match_won else "cry")
                time.sleep(2.0)
                adb.tap(360, 1100) # Tap OK to return home
                state = AppState.RETURNING_HOME
                
            elif state == AppState.RETURNING_HOME:
                if screen_state.name == "HOME_SCREEN":
                    logger.info("Returned to Home Screen.")
                    state = AppState.HOME_SCREEN
                else:
                    logger.info("Waiting to return home...")
                    adb.tap(360, 1100) # Spam OK in case
                    time.sleep(2.0)
                    
            # Diagnostics
            if frame_count % 30 == 0:
                hand = game_state.hand if game_state else []
                state_name = screen_state.name if screen_state else "N/A"
                elx = pipeline.pipeline.strategy.elixir.player_elixir if hasattr(pipeline.pipeline.strategy, 'elixir') else '?'
                logger.debug(f"State: {state.name} | Screen: {state_name} | FPS: {fps:.1f} | Elixir: {elx}")
                
            frame_count += 1
            
        except KeyboardInterrupt:
            logger.info("Play mode safely shut down by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in play loop: {e}")
            traceback.print_exc()
            time.sleep(2)


def run_manage_mode(adb, navigator, collection_reader, deck_builder, build_deck=False):
    """Executes collection management tasks (one-shot)."""
    logger.info("Entering MANAGEMENT MODE.")
    state = AppState.FIRST_BOOT
    
    # Wait for home screen
    for _ in range(10):
        frame = adb.capture_screen()
        if frame is None:
            time.sleep(1)
            continue
            
        # Simplified home check
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        nav_roi = hsv[1180:1260, 50:670]
        blue_mask = cv2.inRange(nav_roi, np.array([100, 100, 50]), np.array([130, 255, 255]))
        if nav_roi.size > 0 and (cv2.countNonZero(blue_mask) / (nav_roi.shape[0] * nav_roi.shape[1])) > 0.05:
            logger.info("Home screen detected.")
            state = AppState.HOME_SCREEN
            break
        
        logger.info("Waiting for home screen...")
        navigator.recover()
        time.sleep(2)
        
    if state != AppState.HOME_SCREEN:
        logger.error("Could not reach home screen. Aborting management tasks.")
        return
        
    logger.info("Navigating to Collection...")
    navigator.go_to_collection()
    time.sleep(2)
    
    if build_deck:
        logger.info("Building optimal deck...")
        deck_builder.auto_build_deck()
    else:
        logger.info("Scanning collection for upgrade suggestions...")
        deck_builder.scan_entire_collection()
        deck_builder._print_upgrade_suggestions()
        
    logger.info("Returning to Home...")
    navigator.go_to_battle()
    logger.info("Management Mode Complete.")


def main():
    parser = argparse.ArgumentParser(description="TITAN S-CLASS Live Agent")
    parser.add_argument("--dashboard", action="store_true", help="Launch the Web Dashboard")
    parser.add_argument("--mode", type=str, choices=["play", "manage"], default="play", help="Operating Mode")
    parser.add_argument("--build-deck", action="store_true", help="Auto-build an optimal deck (Manage mode only)")
    args = parser.parse_args()

    if args.dashboard:
        logger.info("Starting TITAN Dashboard Server...")
        start_dashboard(get_dashboard_frame, get_dashboard_telemetry)

    logger.info("=" * 50)
    logger.info(f" TITAN S-CLASS: {args.mode.upper()} MODE")
    logger.info("=" * 50)

    logger.info("Initializing ADB Controller...")
    adb = ADBController("127.0.0.1:5555")

    # In Management mode, we don't strictly need the async ML pipeline running,
    # but UINavigator uses some cv2, so we load what's necessary.
    import cv2
    import numpy as np

    logger.info("Initializing Management Modules...")
    navigator = UINavigator(adb)
    collection_reader = CollectionReader()
    deck_builder = DeckBuilder(adb, navigator, collection_reader)

    if args.mode == "manage":
        run_manage_mode(adb, navigator, collection_reader, deck_builder, args.build_deck)
        return

    # Play mode requires the ML pipeline
    logger.info("Loading AI Models (Async)...")
    pipeline = AsyncEngine(MODEL_PATH, process_every_n=4)
    pipeline.start()
    visualizer = Visualizer()

    logger.info("System Ready. Monitoring live feed...")
    
    try:
        run_play_mode(adb, pipeline, visualizer, navigator, deck_builder)
    finally:
        if hasattr(pipeline, "stop"):
            pipeline.stop()


if __name__ == "__main__":
    main()

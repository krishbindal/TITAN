"""
TITAN Self-Learning Module: Data Collector
Passively watches gameplay and records the screen states to create 
a Behavioral Cloning / Imitation Learning dataset.
"""

import time
import os
import json
import cv2
import traceback
import argparse
from datetime import datetime

from core.adb_controller import ADBController
from capture.adb_capture import AdbCapture
from engine.pipeline import Pipeline
from configs.settings import MODEL_PATH
from vision.visualizer import Visualizer

def main():
    parser = argparse.ArgumentParser(description="TITAN S-CLASS Imitation Learning Recorder")
    args = parser.parse_args()

    print("=" * 50)
    print(" TITAN: WATCH AND LEARN (PASSIVE DATA COLLECTION)")
    print("=" * 50)

    # Setup directories
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "data/gameplay_logs"
    frame_dir = os.path.join(log_dir, f"session_{session_id}")
    os.makedirs(frame_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"session_{session_id}.jsonl")

    print("Initializing ADB Controller & Vision Models...")
    capture = AdbCapture("127.0.0.1:5555")
    adb = ADBController("127.0.0.1:5555", capture_backend=capture)

    print("Loading AI Models (Vision Only)...")
    # We only need the pipeline for Vision + State parsing. No actions will be sent.
    pipeline = Pipeline(MODEL_PATH)

    print(f"System Ready. Waiting for GAMEPLAY to begin...")
    print(f"Data will be saved to: {log_file}")
    print(f"Frames will be saved to: {frame_dir}")

    consecutive_failures = 0
    max_consecutive_failures = 30
    frame_count = 0
    recorded_frames = 0

    while True:
        try:
            start_time = time.time()
            
            # 1. Capture screen
            frame = adb.capture_screen()
            if frame is None:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print("\n[TITAN] Too many capture failures. Attempting reconnect...")
                    if adb.reconnect():
                        consecutive_failures = 0
                        continue
                    else:
                        print("[TITAN] Could not reconnect. Waiting 10s...")
                        time.sleep(10)
                        consecutive_failures = 0
                        continue
                time.sleep(0.1)
                continue

            consecutive_failures = 0

            # 2. Process frame through TITAN AI
            game_state, _, screen_state, _ = pipeline.process_frame(frame)

            # 3. Only record during active GAMEPLAY
            if screen_state.name == "GAMEPLAY" and game_state is not None:
                timestamp = int(time.time() * 1000)
                frame_filename = f"{timestamp}.jpg"
                frame_path = os.path.join(frame_dir, frame_filename)
                
                # Save Frame (Resize slightly to save space if needed, but original is better for NN)
                cv2.imwrite(frame_path, frame)
                
                # Extract Elixir (if available via tracker)
                elixir = pipeline.strategy.elixir.player_elixir if hasattr(pipeline.strategy, 'elixir') else 0.0
                
                # Serialize GameState
                state_data = {
                    "timestamp": timestamp,
                    "frame_file": frame_filename,
                    "elixir": elixir,
                    "hand": game_state.hand,
                    "troops": [
                        {
                            "name": t.name,
                            "x": t.x,
                            "y": t.y,
                            "is_ally": "ally" in t.name or "ally" in str(t.type)
                        } for t in game_state.troops
                    ]
                }
                
                # Write to JSONL
                with open(log_file, "a") as f:
                    f.write(json.dumps(state_data) + "\n")
                    
                recorded_frames += 1
                
                # Console output every ~2 seconds
                if recorded_frames % 5 == 0:
                    print(f"[TITAN RECORDING] Captured {recorded_frames} frames. Elixir: {elixir:.1f} | Hand: {game_state.hand}")
                    
            elif frame_count % 30 == 0:
                print(f"[TITAN] Waiting for match... (Current Screen: {screen_state.name})")

            # Throttle to ~2-3 FPS to avoid gigabytes of data and excessive CPU
            elapsed = time.time() - start_time
            sleep_time = max(0, 0.4 - elapsed)
            time.sleep(sleep_time)
            
            frame_count += 1

        except KeyboardInterrupt:
            print(f"\n[TITAN] Watch and Learn safely stopped. Recorded {recorded_frames} frames.")
            break
        except Exception as e:
            print(f"\n[TITAN] Error in recording loop: {e}")
            traceback.print_exc()
            time.sleep(2)

if __name__ == "__main__":
    main()

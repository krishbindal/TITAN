"""
TITAN S-Class Test — Real-Time Video Analysis
Uses the AsyncEngine for lag-free processing with full
threat assessment and strategy overlays.
"""

import cv2
import os
import time

from configs.settings import MODEL_PATH
from engine.async_engine import AsyncEngine
from vision.screen_classifier import ScreenState


def test_video(video_path):
    print("Loading TITAN Async Engine with S-Class model...")
    engine = AsyncEngine(MODEL_PATH, process_every_n=4)
    engine.start()

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = int(1000 / fps)

    print(f"Playing {video_path} at {fps:.0f} FPS...")
    print("Click on the video window and press 'q' to quit.")

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Ensure frame matches our training size
        frame = cv2.resize(frame, (720, 1280))

        # Submit to async engine (returns instantly with cached results)
        game_state, action, screen_state, suggestion, result_id = engine.submit_frame(frame)

        # --- Draw Overlays ---
        if screen_state == ScreenState.GAMEPLAY and game_state:

            # Draw confirmed tracks
            for troop in game_state.troops:
                x, y = int(troop.x), int(troop.y)
                color = (0, 255, 0) if troop.team == "ally" else (0, 0, 255)

                # Draw dot
                cv2.circle(frame, (x, y), 6, color, -1)

                # Draw name
                label = troop.name.replace("ally_", "").replace("enemy_", "")
                cv2.putText(
                    frame,
                    label,
                    (x - 20, y - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

            # Draw threat report from strategy engine
            report = engine.pipeline.strategy.get_threat_report(game_state)

            # Threat HUD (top-left)
            hud_y = 40
            cv2.putText(
                frame,
                f"L-DPS: {report.left_dps:.0f}  |  R-DPS: {report.right_dps:.0f}",
                (10, hud_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            hud_y += 30

            hot_color = (0, 255, 255) if report.pressure else (200, 200, 200)
            cv2.putText(
                frame,
                f"Hot Lane: {report.hot_lane} | Pressure: {'YES' if report.pressure else 'No'}",
                (10, hud_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                hot_color,
                2,
            )
            # --- DRAW TROOP BOUNDING BOXES ---
            if game_state:
                for troop in game_state.troops:
                    # Determine color based on team
                    color = (0, 0, 255) if troop.team == "enemy" else (255, 0, 0)
                    # We only have center x, y in Troop, so we draw a small box or circle
                    cv2.circle(frame, (int(troop.x), int(troop.y)), 15, color, -1)
                    cv2.putText(
                        frame,
                        troop.name,
                        (int(troop.x) - 20, int(troop.y) - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2,
                    )

            # --- DRAW UI OVERLAYS ---
            # Hand tracking
            hud_y += 30
            hand_str = ", ".join(game_state.hand) if game_state.hand else "None"
            cv2.putText(
                frame,
                f"Hand: {hand_str}",
                (10, hud_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 100, 255),
                2,
            )
            hud_y += 30

            # Action recommendation
            if action:
                # In phase 2/3, action is an ActionCommand
                action_text = f"Strategy: {action.name}"
                cv2.putText(
                    frame,
                    action_text,
                    (10, hud_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 200, 255),
                    2,
                )

                # Draw the target drop location if we are playing a card
                if (
                    action.action.name == "PLAY_CARD"
                    and action.target_x
                    and action.target_y
                ):
                    tx, ty = action.target_x, action.target_y
                    # Draw a cool crosshair
                    cv2.circle(frame, (tx, ty), 15, (0, 255, 255), 2)
                    cv2.line(frame, (tx - 20, ty), (tx + 20, ty), (0, 255, 255), 2)
                    cv2.line(frame, (tx, ty - 20), (tx, ty + 20), (0, 255, 255), 2)
                    cv2.putText(
                        frame,
                        f"DROP: {action.card_to_play}",
                        (tx + 20, ty - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )

                    if frame_count % 60 == 0:
                        debug_path = f"C:/Users/krish/.gemini/antigravity/brain/96eab5f6-2a3f-40f8-98cd-2d62366e2e2d/drop_debug_{frame_count}.jpg"
                        cv2.imwrite(debug_path, frame)

        elif screen_state and screen_state != ScreenState.GAMEPLAY:
            cv2.putText(
                frame,
                f"State: {screen_state.value} (Skipping)",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )

        # FPS counter
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed > 0:
            display_fps = frame_count / elapsed
            cv2.putText(
                frame,
                f"FPS: {display_fps:.1f}",
                (600, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        # Scale down for PC viewing
        display_frame = cv2.resize(frame, (405, 720))
        cv2.imshow("TITAN S-Class Test", display_frame)

        if cv2.waitKey(frame_delay) & 0xFF == ord("q"):
            break

    engine.stop()
    cap.release()
    cv2.destroyAllWindows()
    print(
        f"Finished. Processed {frame_count} frames in {elapsed:.1f}s ({display_fps:.1f} FPS)"
    )


if __name__ == "__main__":
    video_dir = "C:/Users/krish/Music/clash royale"

    if not os.path.exists(video_dir):
        print(f"Cannot find video directory: {video_dir}")
    else:
        videos = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
        if videos:
            print(f"Found {len(videos)} videos. Testing the first one...")
            test_video(os.path.join(video_dir, videos[0]))
        else:
            print("No .mp4 videos found in", video_dir)

import os
import cv2
import traceback
from engine.pipeline import Pipeline

try:
    print("Initializing pipeline...")
    pipeline = Pipeline("models/best.pt")

    video_dir = "C:/Users/krish/Music/clash royale"
    videos = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    video_path = os.path.join(video_dir, videos[0])

    print(f"Testing video: {video_path}")
    cap = cv2.VideoCapture(video_path)

    for i in range(150):
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (720, 1280))
        game_state, action, screen_state = pipeline.process_frame(frame)

        if i % 30 == 0:
            print(
                f"Frame {i}: Screen={screen_state.name} | Action={action.name if action else 'None'} | Hand={game_state.hand if game_state else []}"
            )
            if action and action.action.name == "PLAY_CARD":
                print(
                    f"  -> DROP: {action.card_to_play} at ({action.target_x}, {action.target_y})"
                )

    print("Test finished successfully.")
except Exception as e:
    print("ERROR OCCURRED:")
    traceback.print_exc()

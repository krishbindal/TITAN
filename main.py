import cv2

from configs.settings import MODEL_PATH
from engine.pipeline import Pipeline


def main():

    pipeline = Pipeline(MODEL_PATH)

    import os
    if not os.path.exists("data/raw/screenshot.png"):
        print("Error: data/raw/screenshot.png not found. Please place a screenshot there to test.")
        return

    frame = cv2.imread("data/raw/screenshot.png")

    if frame is None:
        print("Error: Could not read screenshot.png.")
        return

    game_state, action, screen_state, suggestion = pipeline.process_frame(frame)

    print("Screen State:", screen_state)
    print("Game State:", game_state)

    print("\n============================")
    print("Recommended Action")
    print("============================")
    print(action)


if __name__ == "__main__":
    main()

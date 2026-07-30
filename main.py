import cv2

from configs.settings import MODEL_PATH
from engine.pipeline import Pipeline


def main():

    pipeline = Pipeline(MODEL_PATH)

    frame = cv2.imread("data/raw/screenshot.png")

    if frame is None:
        print("Error: Screenshot not found.")
        return

    game_state, action = pipeline.process_frame(frame)

    print(game_state)

    print("\n============================")
    print("Recommended Action")
    print("============================")
    print(action)


if __name__ == "__main__":
    main()

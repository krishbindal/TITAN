import cv2

from engine.titan_engine import TitanEngine
from configs.settings import MODEL_PATH

VIDEO_PATH = "replays/game1.mp4"


def main():

    engine = TitanEngine(MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print("Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_no = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        current_time = frame_no / fps

        output, tracks, events, screen_state = engine.process_frame(
            frame, frame_no, current_time
        )

        for event in events:
            print(event)

        cv2.imshow("Titan", output)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

        frame_no += 1

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

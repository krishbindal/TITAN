import cv2
from replay.replay_manager import ReplayManager

manager = ReplayManager()

videos = manager.list_replays()

print(videos)

if videos:
    replay = manager.load(videos[0])

    while True:
        success, frame = replay.read_frame()

        if not success:
            break

        cv2.imshow("Replay", frame)

        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    replay.release()
    cv2.destroyAllWindows()

from dataforge.video_info import VideoInfo

video = VideoInfo("replays/game1.mp4")

info = video.get_info()

print("===== VIDEO INFO =====")

for key, value in info.items():
    print(f"{key}: {value}")

video.release()

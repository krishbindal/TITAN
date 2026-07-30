from tools.extract_frames import FrameExtractor

extractor = FrameExtractor(
    video_path="replays/game1.mp4", output_folder="data/raw", interval=30
)

extractor.extract()

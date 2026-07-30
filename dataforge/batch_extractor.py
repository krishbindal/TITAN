import os
import cv2
import time

from dataforge.frame_selector import FrameSelector
from dataforge.metadata import ExtractionMetadata
from dataforge.video_info import VideoInfo
from configs.settings import VIDEO_SOURCE_DIR, EXTRACTED_FRAMES_DIR


class BatchExtractor:

    def __init__(self, source_dir=None, output_dir=None):

        self.source_dir = source_dir or VIDEO_SOURCE_DIR
        self.output_dir = output_dir or EXTRACTED_FRAMES_DIR

        self.selector = FrameSelector()

        self.supported_formats = (".mp4", ".mkv", ".webm", ".avi", ".mov")

    def find_videos(self):

        videos = []

        for filename in sorted(os.listdir(self.source_dir)):

            if any(filename.lower().endswith(ext) for ext in self.supported_formats):
                videos.append(filename)

        return videos

    def is_processed(self, video_name):
        """Check if a video has already been processed (for resume support)."""

        video_dir = self._video_output_dir(video_name)
        manifest = os.path.join(video_dir, "metadata.json")

        return os.path.exists(manifest)

    def extract_video(self, video_name):
        """Extract smart frames from a single video."""

        video_path = os.path.join(self.source_dir, video_name)
        video_dir = self._video_output_dir(video_name)

        os.makedirs(video_dir, exist_ok=True)

        # Reset duplicate filter for each video
        self.selector = FrameSelector()

        metadata = ExtractionMetadata()
        metadata.start(video_name)

        # Get video info
        info = VideoInfo(video_path)
        video_data = info.get_info()
        info.release()

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"  ERROR: Cannot open {video_name}")
            return 0

        frame_number = 0
        saved_count = 0

        total_frames = int(video_data["frames"])

        while True:

            success, frame = cap.read()

            if not success:
                break

            if self.selector.should_select(frame, frame_number):

                # Normalize resolution
                frame = self.selector.normalize(frame)

                # Save frame
                filename = f"frame_{saved_count:05d}.jpg"
                filepath = os.path.join(video_dir, filename)

                cv2.imwrite(filepath, frame)

                metadata.add_frame(saved_count, filename, frame_number)

                saved_count += 1

            frame_number += 1

            # Progress every 1000 frames
            if frame_number % 1000 == 0:
                pct = int(frame_number / max(total_frames, 1) * 100)
                print(f"  Progress: {pct}% ({saved_count} frames saved)")

        cap.release()

        metadata.finish()
        metadata.save(os.path.join(video_dir, "metadata.json"))

        return saved_count

    def extract_all(self, skip_processed=True):
        """Process all videos in the source directory."""

        videos = self.find_videos()

        print(f"Found {len(videos)} videos in {self.source_dir}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 60)

        total_frames = 0
        processed = 0
        skipped = 0

        start_time = time.time()

        for i, video_name in enumerate(videos):

            if skip_processed and self.is_processed(video_name):
                print(f"[{i+1}/{len(videos)}] SKIP (already done): {video_name}")
                skipped += 1
                continue

            print(f"[{i+1}/{len(videos)}] Processing: {video_name}")

            count = self.extract_video(video_name)

            total_frames += count
            processed += 1

            elapsed = time.time() - start_time
            avg_time = elapsed / processed
            remaining = avg_time * (len(videos) - i - 1 - skipped)

            print(
                f"  Saved {count} frames | "
                f"Total so far: {total_frames} | "
                f"ETA: {remaining/60:.1f} min"
            )

        print("=" * 60)
        print(f"DONE: {processed} videos processed, {skipped} skipped")
        print(f"Total frames extracted: {total_frames}")
        print(f"Time elapsed: {(time.time() - start_time)/60:.1f} minutes")

        return total_frames

    def _video_output_dir(self, video_name):

        # Strip extension for folder name
        base = os.path.splitext(video_name)[0]

        # Clean filename for directory use
        safe_name = base.replace(" ", "_")[:80]

        return os.path.join(self.output_dir, safe_name)


if __name__ == "__main__":

    extractor = BatchExtractor()
    extractor.extract_all()

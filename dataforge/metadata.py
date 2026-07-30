import json
import os
from datetime import datetime


class ExtractionMetadata:

    def __init__(self):

        self.frames = []

        self.video_name = None
        self.start_time = None
        self.end_time = None

    def start(self, video_name):

        self.video_name = video_name
        self.start_time = datetime.now().isoformat()
        self.frames = []

    def add_frame(self, frame_index, saved_path, original_frame_number):

        self.frames.append(
            {
                "index": frame_index,
                "path": saved_path,
                "original_frame": original_frame_number,
            }
        )

    def finish(self):

        self.end_time = datetime.now().isoformat()

    def save(self, output_path):

        data = {
            "video": self.video_name,
            "started": self.start_time,
            "finished": self.end_time,
            "total_extracted": len(self.frames),
            "frames": self.frames,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def __str__(self):

        return f"{self.video_name}: " f"{len(self.frames)} frames extracted"

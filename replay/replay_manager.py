import os
from replay.replay import Replay


class ReplayManager:
    def __init__(self, folder="replays"):
        self.folder = folder

    def list_replays(self):

        return [file for file in os.listdir(self.folder) if file.endswith(".mp4")]

    def load(self, filename):
        path = os.path.join(self.folder, filename)
        return Replay(path)

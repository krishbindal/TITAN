from battlefield.geometry import ArenaGeometry


class ZoneDetector:

    def __init__(self):

        self.geometry = ArenaGeometry()

    def analyze(self, track):

        x, y = track.latest_position()

        return {"lane": self.geometry.lane(x), "side": self.geometry.side(y)}

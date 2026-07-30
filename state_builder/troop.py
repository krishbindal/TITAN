class Troop:

    def __init__(self, track_id, name, x, y, team="Unknown", confidence=0.0):
        self.track_id = track_id
        self.name = name
        self.x = x
        self.y = y
        self.team = team
        self.confidence = confidence

    def __str__(self):
        return (
            f"[{self.track_id}] "
            f"{self.name} "
            f"({self.x:.1f}, {self.y:.1f}) "
            f"Team={self.team}"
        )

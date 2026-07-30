import math


class Track:

    def __init__(self, track_id, detection, frame_number):

        self.id = track_id

        self.name = detection.name

        self.confidence = detection.confidence

        self.x = detection.x
        self.y = detection.y
        self.width = detection.width
        self.height = detection.height

        self.positions = [detection.center()]

        self.previous_position = detection.center()

        self.stationary_frames = 0

        self.current_action = None

        self.first_seen = frame_number

        self.last_seen = frame_number

        self.missed_frames = 0

        self.active = True

        # Track confirmation — must survive multiple frames
        # before being reported to the rest of the system
        self.confirmed = False

        self.tentative_hits = 1

    def update(self, detection, frame_number):

        current = detection.center()

        px, py = self.previous_position
        cx, cy = current

        distance = math.hypot(cx - px, cy - py)

        if distance < 5:
            self.stationary_frames += 1
        else:
            self.stationary_frames = 0

        self.previous_position = current

        self.positions.append(current)

        self.confidence = detection.confidence
        self.x = detection.x
        self.y = detection.y
        self.width = detection.width
        self.height = detection.height

        self.last_seen = frame_number

        self.missed_frames = 0

        if not self.confirmed:
            self.tentative_hits += 1

    def latest_position(self):

        return self.positions[-1]

    def distance_to(self, detection):

        x1, y1 = self.latest_position()

        x2, y2 = detection.center()

        return math.hypot(x2 - x1, y2 - y1)

    def mark_missed(self):

        self.missed_frames += 1

        if not self.confirmed:
            self.tentative_hits = 0

    def is_confirmed(self):

        return self.confirmed

    def confirm(self):

        self.confirmed = True

    def is_dead(self, max_missed):

        return self.missed_frames > max_missed

    def __str__(self):

        x, y = self.latest_position()

        action = self.current_action.value if self.current_action else "Unknown"

        status = "Confirmed" if self.confirmed else "Tentative"

        return (
            f"Track {self.id} | "
            f"{self.name} | "
            f"({x:.1f}, {y:.1f}) | "
            f"{action} | "
            f"{status}"
        )

from tracker.track import Track
from configs.settings import CONFIRM_FRAMES, MAX_MISSED_FRAMES, TRACK_DISTANCE


class Tracker:

    def __init__(self):

        self.tracks = []
        self.next_id = 1

        self.max_distance = TRACK_DISTANCE
        self.max_missed_frames = MAX_MISSED_FRAMES
        self.confirm_frames = CONFIRM_FRAMES

        # Tentative tracks get removed faster
        self.max_tentative_missed = 2

    def update(self, detections, frame_number):

        matched_tracks = set()
        start_next_id = self.next_id

        # Match detections
        for detection in detections:

            best_track = None
            best_distance = float("inf")

            for track in self.tracks:

                if track.name != detection.name:
                    continue

                distance = track.distance_to(detection)

                if (
                    distance < self.max_distance
                    and distance < best_distance
                    and track.id not in matched_tracks
                ):
                    best_distance = distance
                    best_track = track

            if best_track is not None:

                best_track.update(detection, frame_number)
                matched_tracks.add(best_track.id)

            else:

                self.tracks.append(Track(self.next_id, detection, frame_number))

                self.next_id += 1

        # Mark missed for tracks that were not matched
        for track in self.tracks:
            if track.id not in matched_tracks and track.id < start_next_id:
                # Only mark missed if it's an old track (not one we just appended)
                track.mark_missed()

        # Promote tentative tracks that survived enough frames
        for track in self.tracks:

            if not track.is_confirmed():

                if track.tentative_hits >= self.confirm_frames:
                    track.confirm()

        # Remove dead tracks
        # Confirmed tracks get max_missed_frames tolerance
        # Tentative tracks get removed quickly (likely false positives)
        self.tracks = [track for track in self.tracks if not self._should_remove(track)]

        return self.tracks

    def get_confirmed_tracks(self):

        return [track for track in self.tracks if track.is_confirmed()]

    def _should_remove(self, track):

        if track.is_confirmed():
            return track.is_dead(self.max_missed_frames)

        return track.is_dead(self.max_tentative_missed)

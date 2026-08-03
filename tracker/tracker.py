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

        from knowledge.card_database import CardDatabase

        matched_tracks = set()
        new_tracks = []
        start_next_id = self.next_id

        import numpy as np
        from scipy.optimize import linear_sum_assignment

        # Match detections using Hungarian algorithm
        if len(self.tracks) > 0 and len(detections) > 0:
            cost_matrix = np.full((len(self.tracks), len(detections)), float('inf'))
            for i, track in enumerate(self.tracks):
                for j, detection in enumerate(detections):
                    if CardDatabase.normalize(track.name) == CardDatabase.normalize(detection.name):
                        distance = track.distance_to(detection)
                        if distance < self.max_distance:
                            cost_matrix[i, j] = distance
            
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            matched_detections = set()
            for i, j in zip(row_ind, col_ind):
                if cost_matrix[i, j] != float('inf'):
                    self.tracks[i].update(detections[j], frame_number)
                    matched_tracks.add(self.tracks[i].id)
                    matched_detections.add(j)
                    
            for j, detection in enumerate(detections):
                if j not in matched_detections:
                    new_tracks.append(Track(self.next_id, detection, frame_number))
                    self.next_id += 1
        else:
            for detection in detections:
                new_tracks.append(Track(self.next_id, detection, frame_number))
                self.next_id += 1

        self.tracks.extend(new_tracks)

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

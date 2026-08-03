from world.event import Event, EventType


class EventDetector:

    def __init__(self):

        self.previous_tracks = {}

    def reset(self):
        """Reset tracked state for a new match."""
        self.previous_tracks = {}

    def update(self, tracks, time):

        events = []

        current = {}

        for track in tracks:

            current[track.id] = track

            # Only emit spawn events for confirmed tracks
            if track.id not in self.previous_tracks and track.is_confirmed():

                events.append(
                    Event(EventType.TROOP_SPAWN, time, f"{track.name} appeared")
                )

        for track_id, old_track in self.previous_tracks.items():

            if track_id not in current:

                # Only emit death events for confirmed tracks
                if old_track.is_confirmed():

                    events.append(
                        Event(
                            EventType.TROOP_DIED, time, f"{old_track.name} disappeared"
                        )
                    )

        self.previous_tracks = current

        return events

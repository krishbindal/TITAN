from actions.action import Action


class ActionDetector:

    def detect(self, track):
        from configs.settings import MAX_MISSED_FRAMES

        if track.missed_frames >= MAX_MISSED_FRAMES:
            track.current_action = Action.DEAD
            return Action.DEAD
        elif track.missed_frames > 0:
            return track.current_action or Action.MOVING

        if track.stationary_frames > 12:
            track.current_action = Action.ATTACKING
            return Action.ATTACKING

        if track.current_action == Action.SPAWNING and track.stationary_frames > 0:
            return Action.SPAWNING
        elif len(track.positions) < 2:
            track.current_action = Action.SPAWNING
            return Action.SPAWNING

        track.current_action = Action.MOVING
        return Action.MOVING

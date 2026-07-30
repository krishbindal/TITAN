from actions.action import Action


class ActionDetector:

    def detect(self, track):

        if track.missed_frames > 0:

            track.current_action = Action.DEAD

            return Action.DEAD

        if track.stationary_frames > 12:

            track.current_action = Action.ATTACKING

            return Action.ATTACKING

        if len(track.positions) < 2:

            track.current_action = Action.SPAWNING

            return Action.SPAWNING

        track.current_action = Action.MOVING

        return Action.MOVING

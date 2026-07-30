class FrameScorer:

    def __init__(self):
        self.weights = {
            "troop": 5,
            "spell": 4,
            "building": 6,
            "champion": 8,
            "tower": 5,
            "effect": 2,
        }

    def score(self, detections):

        score = 0

        for detection in detections:

            name = detection.name.lower()

            if "tower" in name:
                score += self.weights["tower"]

            elif "spell" in name:
                score += self.weights["spell"]

            elif "champion" in name:
                score += self.weights["champion"]

            elif "building" in name:
                score += self.weights["building"]

            elif "effect" in name:
                score += self.weights["effect"]

            else:
                score += self.weights["troop"]

        return score

class Predictor:

    def predict(self, situation):

        if situation.attacker == "enemy" and situation.threat == "high":
            return "Immediate defense required"

        if situation.threat == "medium":
            return "Prepare defense"

        return "No urgent action"

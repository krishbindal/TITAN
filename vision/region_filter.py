from configs.settings import GAMEPLAY_ZONE_BOTTOM


class RegionFilter:

    def __init__(self, card_zone_top=None):

        self.card_zone_top = card_zone_top or GAMEPLAY_ZONE_BOTTOM

    def filter(self, detections):

        filtered = []

        for detection in detections:

            if self._is_valid(detection):
                filtered.append(detection)

        return filtered

    def _is_valid(self, detection):

        _, cy = detection.center()

        is_card = detection.name.startswith("card_")

        if is_card and cy < self.card_zone_top:
            return False

        if not is_card and cy > self.card_zone_top:
            return False

        return True

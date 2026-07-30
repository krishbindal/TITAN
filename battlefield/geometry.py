class ArenaGeometry:

    def __init__(self):

        self.width = 576
        self.height = 1024

        self.center_x = self.width / 2

        self.river_y = self.height / 2

    def lane(self, x):

        if x < self.center_x:
            return "Left"

        return "Right"

    def side(self, y):

        if y > self.river_y:
            return "Blue"

        return "Red"

    def crossed_bridge(self, previous_y, current_y):

        return (previous_y > self.river_y and current_y < self.river_y) or (
            previous_y < self.river_y and current_y > self.river_y
        )

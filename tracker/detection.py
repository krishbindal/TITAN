class Detection:

    def __init__(self, name, x, y, width, height, confidence, team=None):

        self.name = name

        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.confidence = confidence

        self.team = team

    def center(self):

        return (self.x + self.width / 2, self.y + self.height / 2)

    def __str__(self):

        return (
            f"{self.name} " f"({self.x}, {self.y}) " f"Confidence={self.confidence:.2f}"
        )

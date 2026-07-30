class Memory:

    def __init__(self):
        self.events = []

    def remember(self, event):
        self.events.append(event)

    def last(self, n=5):
        return self.events[-n:]

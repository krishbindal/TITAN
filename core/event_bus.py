class EventBus:

    def __init__(self):

        self.listeners = {}

    def subscribe(self, event, callback):

        self.listeners.setdefault(event, []).append(callback)

    def emit(self, event, data=None):

        for callback in self.listeners.get(event, []):

            callback(data)

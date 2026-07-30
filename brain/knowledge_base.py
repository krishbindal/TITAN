class KnowledgeBase:

    def __init__(self):
        self.cards = {}

    def add(self, card):
        self.cards[card.name] = card

    def get(self, name):
        return self.cards.get(name)

    def exists(self, name):
        return name in self.cards

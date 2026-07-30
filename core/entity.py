from uuid import uuid4


class Entity:

    def __init__(self):

        self.id = str(uuid4())

        self.components = {}

    def add_component(self, component):

        self.components[type(component)] = component

    def get_component(self, component_type):

        return self.components.get(component_type)

    def has_component(self, component_type):

        return component_type in self.components

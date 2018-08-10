import logging

logger = logging.getLogger(__name__)


class Entity:
    def __init__(self, name, value, entity_value, start, end):
        self.value = value
        self.entity_value = entity_value
        self.name = name
        self.start = start
        self.end = end

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} {self.value} {self.entity_value} {self.start} {self.end}>"

    def to_example(self):
        return dict(start=self.start, end=self.end, value=self.entity_value, entity=self.name)

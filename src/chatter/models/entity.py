import json


class Entity:
    def __init__(self, entity_name):
        self.start = 0
        self.end = 0
        self.value = None
        self.entity = entity_name

    def update(self, replacement, placeholder, text):
        # save off the entity structure
        self.start = text.find(placeholder) + 1
        self.end = self.start + len(replacement)
        self.value = replacement
        return self

    def to_dict(self):
        return dict(start=self.start, end=self.end, value=self.value, entity=self.entity)

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)

import logging
import random
from collections import defaultdict

from chatter.models.placeholder import all_placeholders

logger = logging.getLogger(__name__)


class EntityBase:
    def __init__(self, name, data=None):
        self.name = name
        self.value = None  # The value chosen
        self.values = []  # List of values to choose from
        self.synonyms = defaultdict(list)
        self.used_synonyms = []
        self.load_data(data)

    def load_data(self, data=None):
        if data is not None:
            if isinstance(data, dict):
                for name, value in data.items():
                    # assuming value is a list
                    # {'New York': ['the big apple', 'New York {city?}']}
                    self.values.append(name)
                    self.synonyms[name].extend(value)
                    self.used_synonyms.append(name)
            elif isinstance(data, list):
                [self.load_data(x) for x in data]
            elif isinstance(data, str):
                self.values.append(data)
            else:
                raise RuntimeError(f"Unknown type: {data}")

    def process_data(self, grammars):
        for name in self.used_synonyms:
            values = []
            for value in self.synonyms[name]:
                if '{' in value:
                    all_values = all_placeholders(value, grammars)
                    values.extend(all_values)
                else:
                    values.append(value)
            self.synonyms[name] = values

        values = []
        for value in self.values:
            if '{' in value:
                all_values = all_placeholders(value, grammars)
                values.extend(all_values)
            else:
                values.append(value)
        self.values = values

    def choose(self, exclude: list=None):
        if not exclude:
            exclude = []

        exclude_set = set(exclude)
        available_set = set(self.values)

        available = available_set - exclude_set
        if not available:
            return None

        self.value = random.choice(list(available))
        return self.value

    def is_entity(self):
        return isinstance(self, Entity)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} {self.value} n_items={len(self.values)}"


class Entity(EntityBase):
    def __init__(self, name, data=None):
        self.start = 0
        self.end = 0
        super().__init__(name, data)

    def update(self, placeholder_text: str, text: str):
        # TODO: Better tracking, and record already used values, etc
        self.value = random.choice(self.values)
        if self.value in self.synonyms:
            self.value = random.choice(self.synonyms[self.value] + [self.value])

        self.start = text.find(placeholder_text) + 1
        self.end = self.start + len(self.value)
        return self

    def to_example(self):
        return dict(start=self.start, end=self.end, value=self.value, entity=self.name)


class Grammar(EntityBase):
    def update(self, placeholder_text: str, text: str):
        # TODO: better way of tracking/choosing
        self.value = random.choice(self.values)

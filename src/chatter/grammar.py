import logging
import random
from collections import defaultdict

from chatter.placeholder import get_all_placeholder_values

logger = logging.getLogger(__name__)


def process_template(template, grammars):
    values = []
    if '{' in template:
        all_values = get_all_placeholder_values(template, grammars)
        values.extend(all_values)
    else:
        values.append(template)
    return values


class Grammar:
    def __init__(self, name, intent=None, is_entity=False):
        self.name = name
        self.value = None  # The value chosen
        self.entity_value = None  # value that is exported to the json file
        self.choices = []  # List of values to choose from
        self.synonyms = defaultdict(list)
        self.used_synonyms = []
        self.intent = intent
        self.is_entity = is_entity

    def load_data(self, data=None):
        if data is not None:
            if isinstance(data, dict):
                for name, value in data.items():
                    # assuming value is a list
                    # {'New York': ['the big apple', 'New York {city?}']}
                    self.choices.append(name)
                    if isinstance(value, list):
                        for x in value:
                            self.synonyms[name].extend(process_template(x, self.intent.grammars))
                    else:
                        self.synonyms[name].extend(value.choices)
                    self.used_synonyms.append(name)
            elif isinstance(data, list):
                [self.load_data(x) for x in data]
            elif isinstance(data, str):
                if '{' in data:
                    dname = data.strip("{}?")
                    if dname in self.intent.grammars:
                        self.load_data({dname: self.intent.grammars[dname]})
                    else:
                        values = process_template(data, self.intent.grammars)
                        self.synonyms[self.name].extend(values)
                        self.choices.extend(values)
                else:
                    self.choices.append(data)
            else:
                raise RuntimeError(f"Unknown type: {data}")

    def update(self, placeholder_text: str, text: str, index: int = None):
        if index is None:
            self.value = random.choice(self.choices)
        else:
            self.value = self.choices[index]

        # check to see if we need a synonym
        name = placeholder_text.strip('{}?')
        if name in self.intent.grammars and self.value in self.intent.grammars[name].synonyms:
            self.entity_value = self.value
            if self.intent.grammars[name].synonyms[self.entity_value]:
                self.value = random.choice(self.intent.grammars[name].synonyms[self.entity_value])

        text = text.replace(placeholder_text, self.value, 1)

        if self.entity_value is None:
            self.entity_value = self.value
        return text

    def choose(self, exclude: list=None):
        if not exclude:
            exclude = []

        exclude_set = set(exclude)
        available_set = set(self.choices)

        available = available_set - exclude_set
        if not available:
            return None

        self.value = random.choice(list(available))
        return self.value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} {self.value} n_items={len(self.choices)}"


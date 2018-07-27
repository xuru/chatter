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
                        self.synonyms[name].extend(value)
                    self.used_synonyms.append(name)
            elif isinstance(data, list):
                [self.load_data(x) for x in data]
            elif isinstance(data, str):
                if '{' in data:
                    dname = data.strip("{}?")
                    values = process_template(data, self.intent.grammars)

                    if dname in self.intent.grammars:
                        self.synonyms[dname] = self.intent.grammars[dname].choices
                    else:
                        self.synonyms[self.name].extend(values)
                    self.used_synonyms.append(self.name)
                    self.choices.extend(values)
                else:
                    self.choices.append(data)
            else:
                raise RuntimeError(f"Unknown type: {data}")

    def update(self, placeholder_text: str, text: str, value: int = None):
        if value is None:
            self.value = random.choice(self.choices)
        else:
            self.value = self.choices[value]

        if self.value in self.synonyms:
            text = text.replace(placeholder_text, random.choice(self.synonyms[self.value]))
        else:
            text = text.replace(placeholder_text, self.value)
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


import json
import logging
import random
from collections import defaultdict
from functools import reduce
from typing import Union, Type, List, Dict

from chatter.parser import load_yaml
from chatter.utils.regex import REPLACEMENT_PATTERN
from chatter.models.entity import Grammar, Entity
from chatter.models.placeholder import Placeholder
from chatter.utils.digest import list_digest

logger = logging.getLogger(__name__)


class RasaBase:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.texts = []
        self.grammars = {}
        self.synonyms = defaultdict(list)

    def load(self, intent_data):
        # self.domain = intent_data['domain']
        self.texts = intent_data['text']

        # grammars
        self.process_data(Grammar, intent_data['grammars'])
        self.process_data(Entity, intent_data['entities'])

        # Update grammars and placeholders, now that we have them all
        for obj in self.grammars.values():
            obj.process_data(self.grammars)

        # Get all the synonyms
        for obj in self.grammars.values():
            self.synonyms.update(obj.synonyms)

        return self

    def process_data(self, cls: Type[Union[Grammar, Entity]], data):
        if isinstance(data, list):
            for obj in data:
                self.process_data(cls, obj)
        else:
            for name, value in data.items():
                self.grammars[name] = cls(name, value)


class RasaNLUIntent(RasaBase):
    def __init__(self, intent_name):
        super().__init__(intent_name)
        self.entities_used = []
        self.synonyms_used = {}
        self.digests_used = []

    def to_json(self, num=1):
        return json.dumps(self.generate(num), indent=2)

    def sentences(self, num=1):
        self.validate_num(num)
        if not self.texts:
            raise RuntimeError("Need text templates to process Rasa examples!")
        return [example['text'] for example in self.generate_examples(num)]

    def generate(self, num=1):
        self.validate_num(num)
        if not self.texts:
            raise RuntimeError("Need text templates to process Rasa examples!")

        examples = self.generate_examples(num)

        return dict(
            rasa_nlu_data=dict(
                regex_features=self.regex_features(),
                entity_synonyms=self.entity_synonyms(),
                common_examples=examples
            ))

    def get_possible_combinations(self):
        rv = {}
        for text in self.texts:
            placeholders = self.get_placeholders(text)
            rv[text] = reduce(lambda x, y: x * y, [len(x.grammar.values) for x in placeholders])
        return rv

    def validate_num(self, num):
        valid = True
        for text, combos in self.get_possible_combinations().items():
            if num > combos:
                valid = False
                break
        if valid is False:
            raise RuntimeError(f"Max number of combinations exceded. Max is {combos}")

    def generate_examples(self, num=1) -> List[dict]:
        return [self.common_example(self.choose_text()) for _ in range(num)]

    def common_example(self, text=None) -> dict:
        # reset, to track what entities were used for only this example text
        self.entities_used = []

        if text is None:
            text = self.choose_text()
        text = self.process_text(text)

        common_example = dict(
            text=text,
            intent=self.name,
            entities=[e.to_example() for e in self.entities_used])
        return common_example

    def entity_synonyms(self):
        # TODO
        rv = []
        for name, value in self.synonyms_used.items():
            rv.append(dict(value=name, synonyms=value))
        return rv

    def regex_features(self):
        return [
            dict(name="zipcode", pattern="[0-9]{5}")
        ]

    def choose_text(self) -> str:
        return random.choices(self.texts)[0]

    def process_text(self, text: str):
        placeholders = self.get_placeholders(text)

        unique = False
        while not unique:
            for placeholder in placeholders:
                text = placeholder.process(text)

            combination = [x.grammar.value for x in placeholders]
            digest = list_digest(combination)
            if digest not in self.digests_used:
                self.digests_used.append(digest)
                unique = True

        return text

    def get_placeholders(self, text):
        rv = []
        for placeholder_text in REPLACEMENT_PATTERN.findall(text):
            placeholder = Placeholder(placeholder_text)

            grammar = self.grammars[placeholder.name]
            if isinstance(grammar, Entity):
                self.entities_used.append(grammar)

            for name in grammar.used_synonyms:
                self.synonyms_used[name] = self.synonyms[name]
            placeholder.grammar = grammar
            rv.append(placeholder)
        return rv


def intents_loader(stream):
    intents = {}
    data = load_yaml(stream)

    # usually only one intent perfile, but can do multiple
    for intent_name, intent_data in data.items():
        intents[intent_name] = RasaNLUIntent(intent_name).load(intent_data)
    return intents

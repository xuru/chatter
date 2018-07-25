import copy
import json
import logging
import random
from collections import defaultdict
from functools import reduce
from typing import Union, Type, List

from chatter.models.common_example import CommonExample
from chatter.models.entity import Grammar, Entity
from chatter.parser import load_yaml
from chatter.utils.digest import get_digest

logger = logging.getLogger(__name__)


class RasaBase:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.texts = []
        self.grammars = {}
        self.synonyms = defaultdict(list)
        self._texts_available = []

    def load(self, intent_data):
        # self.domain = intent_data['domain']
        self.texts = intent_data['text']
        self._texts_available = copy.copy(self.texts)  # keep a copy for our book keeping
        if not self.texts:
            raise RuntimeError("Need text templates to process Rasa examples!")

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
        self.used_combinations = defaultdict(list)

    def to_json(self, num=1):
        return json.dumps(self.generate(num), indent=2)

    def sentences(self, num=1):
        self.validate_num(num)
        return [example.text for example in self.generate_examples(num)]

    def generate(self, num=1):
        self.validate_num(num)

        # generate all examples
        examples = self.generate_examples(num)

        # save off all synonyms we used
        for example in examples:
            self.synonyms_used.update(example.synonyms_used)

        return dict(
            rasa_nlu_data=dict(
                regex_features=[dict(name="zipcode", pattern="[0-9]{5}")],
                entity_synonyms=self.entity_synonyms(),
                common_examples=[example.to_dict() for example in examples]
            ))

    def generate_examples(self, num=1) -> List[CommonExample]:
        examples = []
        for index in range(num):
            text = self.choose_text()
            key = get_digest(text)

            example = CommonExample(text, self)

            # save off what combination we are going to use
            combination = example.process(self.used_combinations[key])
            self.used_combinations[key].append(combination)

            examples.append(example)
        return examples

    def _get_num_combos_for_text(self, text):
        example = CommonExample(text, self)
        combos = example.combinations()
        return reduce(lambda x, y: x * y, combos.values())

    def get_possible_combinations(self):
        rv = {}
        for text in self.texts:
            rv[text] = self._get_num_combos_for_text(text)
        return rv

    def validate_num(self, num):
        total = sum([self._get_num_combos_for_text(text) for text in self.texts])
        if num > total:
            raise RuntimeError(f"Max number of combinations exceded. Max is {total}")

    def entity_synonyms(self):
        rv = []
        for name, value in self.synonyms_used.items():
            rv.append(dict(value=name, synonyms=value))
        return rv

    def choose_text(self) -> str:
        found = False
        while not found:
            text = random.choice(self._texts_available)
            key = get_digest(text)
            if len(self.used_combinations[key]) >= self._get_num_combos_for_text(text):
                self._texts_available.remove(text)
                if not self._texts_available:
                    raise RuntimeError("Exceeded number of available combinations for texts")
            else:
                return text


def intents_loader(stream):
    intents = {}
    data = load_yaml(stream)

    # usually only one intent perfile, but can do multiple
    for intent_name, intent_data in data.items():
        intents[intent_name] = RasaNLUIntent(intent_name).load(intent_data)
    return intents

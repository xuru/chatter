import copy
import json
import logging
import random
from collections import defaultdict
from functools import reduce
from typing import List

from chatter.common_example import CommonExample
from chatter.exceptions import CombinationsExceededError, PlaceholderError
from chatter.grammar import Grammar
from chatter.utils.yaml import load_yaml

logger = logging.getLogger(__name__)


class RasaBase:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.texts = []
        self.grammars = {}
        self.synonyms = defaultdict(list)
        self._texts_available = []
        self.grammar_queue = []

    def load(self, intent_data):
        # self.domain = intent_data['domain']
        self.texts = intent_data['text']
        self._texts_available = copy.copy(self.texts)  # keep a copy for our book keeping
        if not self.texts:
            raise RuntimeError("Need text templates to process Rasa examples!")

        # grammars
        self.process_grammars(intent_data['grammars'])
        while self.grammar_queue:
            self.process_grammars(self.grammar_queue.pop())

        self.process_grammars(intent_data['entities'], is_entity=True)

        # Get all the synonyms
        for grammar in self.grammars.values():
            self.synonyms.update(grammar.synonyms)
        return self

    def process_grammars(self, data, is_entity=False):
        if isinstance(data, list):
            for obj in data:
                self.process_grammars(obj, is_entity)
        else:
            for name, value in data.items():
                name = name.strip('{}?')
                try:
                    self.grammars[name] = Grammar(name, self, is_entity)
                    self.grammars[name].load_data(value)
                except PlaceholderError:
                    self.grammar_queue.append(data)


class RasaNLUIntent(RasaBase):
    def __init__(self, intent_name):
        super().__init__(intent_name)
        self.entities_used = []
        self.synonyms_used = {}
        self.digests_used = []
        self.used_combinations = defaultdict(list)

    def to_json(self, num=0):
        if num == 0:
            num = sum(self.get_possible_combinations().values())
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

    def entity_synonyms(self):
        rv = []
        for name, value in self.synonyms_used.items():
            rv.append(dict(value=name, synonyms=value))
        return rv

    def generate_examples(self, num=1) -> List[CommonExample]:
        rv = []
        logger.debug(f"Generating {num} examples")
        for num in range(num):
            if num % 10:
                logger.debug(f"Processed {num} examples")
            try:
                example = CommonExample(self.choose_text(), self)
            except CombinationsExceededError as error:
                logger.warning(f"Exceeded the number of combinations.  Limiting to {num}")
                return rv

            example.process()
            rv.append(example)
        return rv

    def _get_num_combos_for_text(self, text):
        combos = CommonExample(text, self).get_combinations()
        if combos:
            return reduce(lambda x, y: x * y, combos.values())
        return 1

    def get_possible_combinations(self):
        return {text: self._get_num_combos_for_text(text) for text in self.texts}

    def validate_num(self, num):
        total = sum(self.get_possible_combinations().values())
        if num > total:
            raise RuntimeError(f"Max number of combinations exceded. Max is {total}")

    def choose_text(self) -> str:
        found = False
        while not found:
            text = random.choice(self._texts_available)
            if len(self.used_combinations[text]) >= self._get_num_combos_for_text(text):
                self._texts_available.remove(text)
                if not self._texts_available:
                    raise CombinationsExceededError("Exceeded number of available combinations for texts")
            else:
                return text


def intents_loader(stream):
    intents = {}
    data_set = load_yaml(stream)

    # usually only one intent perfile, but can do multiple
    for data in data_set:
        for intent_name, intent_data in data.items():
            intents[intent_name] = RasaNLUIntent(intent_name).load(intent_data)
    return intents

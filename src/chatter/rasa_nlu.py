import copy
import json
import logging
import math
import queue
import random
from collections import defaultdict, OrderedDict
from typing import List

from chatter.common_example import CommonExample
from chatter.exceptions import PlaceholderError
from chatter.grammar import Grammar
from chatter.parser import TextParser, PATTERN_RESERVED_CHARS

logger = logging.getLogger(__name__)


class Texts:
    def __init__(self):
        self.available = []
        self.used = []
        self.important_count = 0

    @property
    def count(self) -> int:
        return sum(self.available + self.used)

    def load(self, texts):
        # self.domain = intent_data['domain']
        if not texts:
            raise RuntimeError("Need text templates to process Intents!")

        for text in texts:
            if isinstance(text, str):
                self.available.append(copy.copy(text))

            elif isinstance(text, (OrderedDict, dict)):
                for name, value in text.items():
                    if name == 'important':
                        self.available[0:0] += value
                        self.important_count += 1
            else:
                raise RuntimeError(f"Unknown type in 'texts' section: {text}")

    def invalidate_text(self, text):
        if text in self.available:
            self.available.remove(text)
            self.used.append(text)

    def get(self):
        """
        Pick an unused text by poping it off the top of the stack

        :return: str - The next unused text
        """
        while self.available:
            text = self.available.pop()
            self.used.append(text)
            yield text

    def get_used(self):
        """
        Randomly pick from the "used" list.

        :return: str - A random text
        """
        if self.used:
            return random.choice(self.used)


class Intent:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.texts: Texts = None
        self.text_parsers: List[TextParser] = []
        self.parser_map = {}
        self.grammars = {}
        self.synonyms = defaultdict(list)
        self.grammar_queue = queue.Queue()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} n_texts={self.texts.count}>"

    def get_possible_combinations(self):
        return {parser.text: parser.possible_combinations for parser in self.text_parsers}

    def get_possible_combination_count(self):
        return sum(self.get_possible_combinations().values()) or 1

    def get_parser_combination(self, parser: TextParser):
        try:
            return next(parser.combinator.get())
        except StopIteration:
            self.texts.invalidate_text(parser.text)
            return parser.combinator.get_used()

    def get_combinations(self, num):
        # ensure that priority grammars are moved up the list
        for parser in self.text_parsers:
            parser.ensure_priority_combinations(num)

        for index in range(num):
            text = self.choose_text()
            parser = self.parser_map[text]
            yield text, self.get_parser_combination(parser)

    def _get_minimum_num(self, num):
        if num == 0:
            num = self.get_possible_combination_count()

        min_combos = sum([parser.combinator.get_min_combinations() for parser in self.text_parsers])
        min_combos += self.texts.important_count
        if num < min_combos:
            logger.warning(f"Number of generated examples increased due to priority grammars to {min_combos}")
            return min_combos
        return num

    def sentences(self, num=1, combinations=None):
        num = self._get_minimum_num(num)

        if combinations is None:
            combinations = defaultdict(set)
            for text, seq in self.get_combinations(num):
                combinations[text].add(seq)

        for text, seqs in combinations.items():
            if seqs:
                for seq in seqs:
                    parser = self.parser_map[text]
                    yield parser.process(seq, self.grammars)
            else:
                yield text

    def load(self, intent_data):
        # self.domain = intent_data['domain']
        self.texts = Texts()
        self.texts.load(intent_data['text'])

        # grammars
        self.process_grammars(intent_data['grammars'])
        self.process_grammars(intent_data['entities'], is_entity=True)

        retries = {}
        # process grammars that were probably not loaded in time
        while not self.grammar_queue.empty():
            data = None
            try:
                data = self.grammar_queue.get()
                self.process_grammars(data, raise_on_error=True)
            except PlaceholderError as err:
                if self.grammar_queue.empty():
                    # exhausted all options...
                    raise err
                else:
                    for n in data.keys():
                        if n in retries:
                            retries[n] += 1
                        else:
                            retries[n] = 1
                        if retries[n] > 3:
                            raise err
                    self.grammar_queue.put(data)

        # Get all the synonyms
        for grammar in self.grammars.values():
            self.synonyms.update(grammar.synonyms)

        for text in self.texts.available:
            self.text_parsers.append(TextParser(text, self.grammars))
            self.parser_map[text] = self.text_parsers[-1]

        return self

    def process_grammars(self, data, is_entity=False, raise_on_error=False):
        if isinstance(data, list):
            for obj in data:
                self.process_grammars(obj, is_entity)
        else:
            for name, value in data.items():
                name = name.strip(PATTERN_RESERVED_CHARS)
                try:
                    self.grammars[name] = Grammar(name, self, is_entity)
                    self.grammars[name].load_data(value)
                except PlaceholderError as err:
                    if raise_on_error:
                        err.grammar_name = name
                        raise err
                    self.grammar_queue.put(data)

    def choose_text(self) -> str:
        try:
            return next(self.texts.get())
        except StopIteration:
            return self.texts.get_used()


class RasaNLUIntent(Intent):
    def __init__(self, intent_name):
        super().__init__(intent_name)
        self.synonyms_used = {}
        self.training_examples = []
        self.testing_examples = []

    def process(self, num=0, test_ratio=0):
        num = self._get_minimum_num(num)
        testing_count = math.ceil(num * (test_ratio / 100))
        training_count = num - testing_count

        if testing_count:
            logger.info(
                f"Processing {self.name} with {num} examples ({testing_count} testing)")

        for index, example in enumerate(self.examples(num)):
            self.synonyms_used.update(example.synonyms_used)
            if index >= training_count:
                self.testing_examples.append(example)
            else:
                self.training_examples.append(example)

    def json(self, test=False):
        if test is True:
            example_dicts = [e.to_dict() for e in self.testing_examples]
        else:
            example_dicts = [e.to_dict() for e in self.training_examples]

        rv = dict(
            rasa_nlu_data=dict(
                regex_features=[],
                entity_synonyms=self.entity_synonyms(),
                common_examples=example_dicts
            ))
        return json.dumps(rv, indent=2)

    def entity_synonyms(self):
        return [dict(value=name, synonyms=value) for name, value in self.synonyms_used.items()]

    def examples(self, num=0, combinations=None):
        num = self._get_minimum_num(num)
        if combinations is None:
            for text, seq in self.get_combinations(num):
                parser = self.parser_map[text]
                example = CommonExample(self)
                example.process(parser, seq)
                yield example

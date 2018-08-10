import copy
import json
import logging
import queue
import random
from collections import defaultdict

from chatter.common_example import CommonExample
from chatter.exceptions import CombinationsExceededError, PlaceholderError
from chatter.grammar import Grammar
from chatter.parser import TextParser

logger = logging.getLogger(__name__)


class Intent:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.texts = []
        self.text_parsers = []
        self.grammars = {}
        self.synonyms = defaultdict(list)
        self.grammar_queue = queue.Queue()

        self._texts_available = []

    def get_possible_combinations(self):
        return {parser.text: parser.possible_combinations for parser in self.text_parsers}

    def get_total_possible_combinations(self):
        return sum(self.get_possible_combinations().values()) or 1

    def get_combinations(self, num=1):
        if num == 0:
            num = self.get_total_possible_combinations()

        for _ in range(num):
            text = self.choose_text()
            parser = self.text_parsers[self.texts.index(text)]
            seq = self.get_parser_combination(parser)
            yield text, seq

    def sentences(self, num=1, combinations=None):
        if num == 0:
            num = self.get_total_possible_combinations()

        if combinations is None:
            combinations = defaultdict(set)
            for text, seq in self.get_combinations(num):
                combinations[text].add(seq)

        for text, combinations in combinations.items():
            if combinations:
                for seq in combinations:
                    parser = self.text_parsers[self.texts.index(text)]
                    yield parser.process(seq, self.grammars)
            else:
                yield text

    def get_parser_combination(self, parser: TextParser):
        try:
            seq = parser.get_unused_combination()
            return seq
        except CombinationsExceededError as error:
            if self._texts_available:
                self._texts_available.remove(parser.org_text)
            logger.warning(f"Exceeded combinations available for: {parser.org_text}")
            return parser.get_used_combination()

    def load(self, intent_data):
        # self.domain = intent_data['domain']
        self.texts = intent_data['text']
        self._texts_available = copy.copy(self.texts)  # keep a copy for our book keeping

        if not self.texts:
            raise RuntimeError("Need text templates to process Intents!")

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

        self.text_parsers = [TextParser(text, self) for text in self.texts]

        return self

    def process_grammars(self, data, is_entity=False, raise_on_error=False):
        if isinstance(data, list):
            for obj in data:
                self.process_grammars(obj, is_entity)
        else:
            for name, value in data.items():
                name = name.strip('{}?')
                try:
                    self.grammars[name] = Grammar(name, self, is_entity)
                    self.grammars[name].load_data(value)
                except PlaceholderError as err:
                    if raise_on_error:
                        err.grammar_name = name
                        raise err
                    self.grammar_queue.put(data)

    def choose_text(self) -> str:
        if not self._texts_available:
            text = random.choice(self.texts)
        else:
            text = random.choice(self._texts_available)
        return text


class RasaNLUIntent(Intent):
    def __init__(self, intent_name):
        super().__init__(intent_name)
        self.entities_used = []
        self.synonyms_used = {}
        self.digests_used = []

    def __repr__(self):
        return f"<RasaNLUIntent {self.name} n_texts={len(self.texts)}>"

    def to_json(self, num=0):
        if num == 0:
            num = sum(self.get_possible_combinations().values())

        # generate all examples
        examples = self.examples(num)

        # save off all synonyms we used
        example_dicts = []
        for example in examples:
            self.synonyms_used.update(example.synonyms)
            example_dicts.append(example.to_dict())

        rv = dict(
            rasa_nlu_data=dict(
                regex_features=[],
                entity_synonyms=self.entity_synonyms(),
                common_examples=example_dicts
            ))
        return json.dumps(rv, indent=2)

    def entity_synonyms(self):
        rv = []
        for name, value in self.synonyms_used.items():
            rv.append(dict(value=name, synonyms=value))
        return rv

    def examples(self, num=1, combinations=None):
        if num == 0:
            num = sum(self.get_possible_combinations().values())

        if combinations is None:
            for text, seq in self.get_combinations(num):
                parser = self.text_parsers[self.texts.index(text)]
                example = CommonExample(self)
                example.process(parser, seq)
                yield example

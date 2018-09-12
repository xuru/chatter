import json
import logging
import math
import queue
from collections import defaultdict

from chatter.common_example import CommonExample
from chatter.exceptions import PlaceholderError, GrammarError
from chatter.grammar import Grammar
from chatter.parser import TextParser, PATTERN_RESERVED_CHARS, Parsers

logger = logging.getLogger(__name__)


class Intent:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.parsers: Parsers = None
        self.grammars = {}
        self.entities = {}
        self.synonyms = defaultdict(list)
        self.grammar_queue = queue.Queue()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} n_texts={len(self.parsers)}>"

    def load(self, intent_data):
        # self.domain = intent_data['domain']
        self.parsers = Parsers()

        # grammars
        self.process_grammars(intent_data['grammars'])
        try:
            self._run_down_queue()
        except PlaceholderError as err:
            logger.warning(f"{err}. Seeing if it's in entities...")
        self.process_grammars(intent_data['entities'], is_entity=True)
        self._run_down_queue(is_entity=True)

        # Get all the synonyms
        for grammar in self.grammars.values():
            self.synonyms.update(grammar.synonyms)

        self.parsers.load(intent_data['text'], self.grammars)

        # special case: if the grammar list is empty, remove the placeholder from the sentence
        dead_grammars = [name for name, grammar in self.grammars.items() if not grammar.choices]
        if dead_grammars:
            raise GrammarError(f"Grammars found without replacement strings: {dead_grammars}")

        return self

    def get_possible_combinations(self):
        return {parser.text: parser.possible_combinations for parser in self.parsers}

    def get_possible_combination_count(self):
        return sum(self.get_possible_combinations().values()) or 1

    def get_parser_combination(self, parser: TextParser):
        rv = parser.combinator.get()
        if rv is None:
            self.parsers.invalidate_text(parser)
            return parser.combinator.get_used()
        return rv

    def get_combinations(self, num):
        for index in range(num):
            parser = self.choose_text()
            try:
                combo = self.get_parser_combination(parser)
            except Exception as err:
                print(err)

            yield parser, combo


    def _get_minimum_num(self, num):
        if num == 0:
            num = self.get_possible_combination_count()

        min_combos = 0
        for parser in self.parsers:
            min_combos += parser.combinator.get_min_combinations()

        # min_combos = sum([parser.combinator.get_min_combinations() for parser in self.parsers])
        min_combos += self.parsers.important_count
        if num < min_combos:
            logger.warning(f"Number of generated examples increased due to priority grammars to {min_combos}")
            return min_combos
        return num

    def sentences(self, num=1, combinations=None):
        num = self._get_minimum_num(num)
        # parser_map = {}

        if combinations is None:
            combinations = list(self.get_combinations(num))

        for parser, seq in combinations:
            yield parser.process(seq, self.grammars)

    def _run_down_queue(self, is_entity=False):
        retries = {}
        # process grammars that were probably not loaded in time
        while not self.grammar_queue.empty():
            data = None
            try:
                data = self.grammar_queue.get()
                self.process_grammars(data, is_entity=is_entity, raise_on_error=True)
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

    def process_grammars(self, data, is_entity=False, raise_on_error=False):
        if isinstance(data, list):
            for obj in data:
                self.process_grammars(obj, is_entity)
        else:
            for name, value in data.items():
                name = name.strip(PATTERN_RESERVED_CHARS)
                try:
                    if name not in self.grammars:
                        self.grammars[name] = Grammar(name, self, is_entity)
                    self.grammars[name].load_data(value)

                    if is_entity:
                        self.entities[name] = self.grammars[name]
                except PlaceholderError as err:
                    if raise_on_error:
                        err.grammar_name = name
                        raise err
                    self.grammar_queue.put(data)

    def choose_text(self) -> TextParser:
        try:
            return next(self.parsers.get_text())
        except StopIteration:
            return self.parsers.get_used()


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

        for parser in self.parsers:
            parser.combinator.reset_combinations()

        if testing_count:
            logger.info(
                f"Processing {self.name} with {num} examples ({testing_count} testing)")

        index = 0
        for example in self.examples(num):
            self.synonyms_used.update(example.synonyms_used)
            if index >= training_count:
                self.testing_examples.append(example)
            else:
                self.training_examples.append(example)
            index += 1

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
        if num == 70:
            print('bob')
        if combinations is None:
            for index in range(num):
                parser = self.choose_text()
                seq = self.get_parser_combination(parser)

                example = CommonExample(self)
                example.process(parser, seq)
                yield example

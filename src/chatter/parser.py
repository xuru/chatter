import copy
import itertools
import random
from random import SystemRandom

from chatter.exceptions import CombinationsExceededError
from chatter.utils.regex import REPLACEMENT_PATTERN


class PlaceHolder:
    pattern: str = None
    optional: bool = False
    name: str = None
    value: str = None
    synonym: str = None
    start: int = 0
    end: int = 0

    def __init__(self, pattern, value=None, synonym=None, start=0, end=0):
        self.pattern = pattern
        self.optional = '?' in pattern
        self.name = pattern.strip("{}?")
        self.value = value
        self.synonym = synonym
        self.start = start
        self.end = end

    def __repr__(self):
        return f"<PlaceHolder {self.name}: {self.value} [{self.start}, {self.end}]>"


class TextParser:
    def __init__(self, text, parent=None):
        self.parent = parent
        self.possible_combinations = 0
        self.org_text = copy.copy(text)
        self._available_combinations = set()
        self._used_combinations = set()

        self.placeholders = [
            PlaceHolder(pattern) for pattern in REPLACEMENT_PATTERN.findall(text)
        ]
        self.names = [p.name for p in self.placeholders]
        self._set_all_possible_combinations()

    def get_unused_combination(self):
        if not self._available_combinations:
            raise CombinationsExceededError()

        combination = self._available_combinations.pop()
        self._used_combinations.add(combination)
        return list(combination)

    def get_used_combination(self):
        if self._used_combinations:
            return list(random.choice(list(self._used_combinations)))

    def _fix_telemetry(self, text, p, value, synonym=None):
        p.value = value
        if synonym:
            p.synonym = synonym
        p.start = text.find(p.pattern)
        p.end = p.start + len(value)
        return p

    def process(self, combination: list, grammars: dict):
        text = copy.copy(self.org_text)
        for index, name in enumerate(self.names):
            choice_index = combination[index]
            p = self.placeholders[index]
            value = grammars[name].choices[choice_index]
            if p.optional:
                # flip a coin
                value = random.choice([value, ''])

            if value in grammars[name].synonyms:
                # TODO: we need a controlled way to do this
                p.synonym = value
                value = random.choice(grammars[name].synonyms[value])
            self._fix_telemetry(text, p, value)
            text = text.replace(p.pattern, value, 1)
            # clear up any whitespace issues...
            text = " ".join(text.split())

        return text

    def _set_all_possible_combinations(self):
        values = []
        self.possible_combinations = 1
        for p in self.placeholders:
            if self.parent.grammars is not None:
                count = len(self.parent.grammars[p.name].choices)
                values.append(list(range(count)))

                self.possible_combinations = self.possible_combinations * count

        if values:
            available_combinations = list(itertools.product(*values))
            cryptorand = SystemRandom()
            cryptorand.shuffle(available_combinations)
            self._available_combinations = set(available_combinations)

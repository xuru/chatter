import copy
import itertools
import logging
import random
from random import SystemRandom

from chatter.exceptions import CombinationsExceededError
from chatter.utils.regex import REPLACEMENT_PATTERN

PATTERN_RESERVED_CHARS = "{}>?"
PATTERN_OPTIONAL = "?"
PATTERN_PRIORITY = ">"

logger = logging.getLogger(__name__)


class PlaceHolder:
    pattern: str = None
    optional: bool = False
    priority: bool = False
    name: str = None
    value: str = None
    synonym: str = None
    start: int = 0
    end: int = 0

    def __init__(self, pattern, value=None, synonym=None, start=0, end=0):
        self.pattern = pattern
        self.optional = PATTERN_OPTIONAL in pattern
        self.priority = PATTERN_PRIORITY in pattern
        self.name = pattern.strip(PATTERN_RESERVED_CHARS)
        self.index_range = 0
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
        self.reset_combinations()

    ################################################################################
    # Combinations
    ################################################################################
    def reset_combinations(self):
        values = []
        self.possible_combinations = 1
        for p in self.placeholders:
            if self.parent.grammars is not None:
                count = len(self.parent.grammars[p.name].choices)
                p.index_range = count
                values.append(list(range(count)))

                self.possible_combinations = self.possible_combinations * count

        if values:
            available_combinations = list(itertools.product(*values))
            cryptorand = SystemRandom()
            cryptorand.shuffle(available_combinations)
            self._available_combinations = set(available_combinations)

    def get_unused_combination(self):
        if not self._available_combinations:
            raise CombinationsExceededError()

        combination = self._available_combinations.pop()
        self._used_combinations.add(combination)
        return list(combination)

    def get_used_combination(self):
        if self._used_combinations:
            return list(random.choice(list(self._used_combinations)))

    def get_min_combinations(self):
        total = sum([p.index_range for p in self.placeholders if p.priority])
        if not total:
            return 0
        return total

    def ensure_priority_combinations(self, num):
        # range of priority grammar must be less then or equal to num
        #

        available_combinations = list(self._available_combinations)
        for priority_index, p in enumerate(self.placeholders):
            if p.priority:
                logger.info(f"Checking: {p.name}:{priority_index}")

                existing = set([x[priority_index] for x in available_combinations[:num]])
                possible = set(range(p.index_range))
                missing = possible - existing
                logger.info(f"  Missing: {missing} == {possible} - {existing}")
                if not missing:
                    continue

                move_list = []
                table_index = len(available_combinations) - 1
                while missing:
                    if available_combinations[table_index][priority_index] in missing:
                        move_list.append(available_combinations[table_index])
                        missing.remove(available_combinations[table_index][priority_index])
                    table_index -= 1
                    if table_index <= 0:
                        raise RuntimeError(f"Unable to find all combinations of priorty grammar {p.name}")

                for combination in move_list:
                    logger.info(f"Moving: {p.name}:{priority_index} - {combination}")
                    available_combinations.insert(0, available_combinations.pop(available_combinations.index(combination)))

                self._available_combinations = set(available_combinations)

    ################################################################################
    # Text processing
    ################################################################################
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

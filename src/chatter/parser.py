import copy
import logging
import random
from collections import OrderedDict
from typing import MutableSequence

from chatter.combinator import Combinator
from chatter.exceptions import PlaceholderError
from chatter.utils.regex import REPLACEMENT_PATTERN

PATTERN_RESERVED_CHARS = "{}>?"
PATTERN_OPTIONAL = "?"
PATTERN_PRIORITY = ">"

logger = logging.getLogger(__name__)


class TextParser:
    def __init__(self, text, grammars=None):
        self._grammars = grammars
        self.placeholders = []
        self.names = []
        self.text = copy.copy(text)
        self.combinator = None

        self.setup_placeholders()

    @property
    def grammars(self):
        return self._grammars

    @grammars.setter
    def grammars(self, grammars):
        self._grammars = grammars

    @property
    def has_priority_grammar(self):
        return any([p.priority for p in self.placeholders])

    @property
    def possible_combinations(self):
        """
        Get the total number of possible combinations

        :return: The total
        """
        return self.combinator.count

    def setup_placeholders(self):
        """
        Extract the placeholders from the text template, and initialize them with grammars if available

        :return: None
        """
        from chatter.placeholder import PlaceHolder

        for pattern in REPLACEMENT_PATTERN.findall(self.text):
            p = PlaceHolder(pattern)

            if self.grammars is not None:
                try:
                    p.index_range = len(self.grammars[p.name].choices)
                except:
                    raise PlaceholderError(grammar_name=p.name, placeholder_text=self.text)
            self.names.append(p.name)
            self.placeholders.append(p)

        self.combinator = Combinator(self.placeholders)

    def process(self, combination: list, grammars: dict):
        """
        Given a dictionary of grammars, use the combination, and transform the text template and return it.

        :param combination: A list of indexes into the grammar dictionary
        :param grammars: A dictionary of grammars with the key being the name of the grammar, and the value is the
         possible choices of that grammar.
        :return: str - A new string with all placeholders replaced with grammars
        """
        text = copy.copy(self.text)
        if self.placeholders:
            for index, name in enumerate(self.names):
                choice_index = combination[index]
                p = self.placeholders[index]
                try:
                    value = grammars[name].choices[choice_index]
                except:
                    print('bob')

                if p.optional:
                    # flip a coin
                    value = random.choice([value, ''])

                for syn in grammars[name].used_synonyms:
                    if value in grammars[name].synonyms[syn]:
                        p.synonym = syn
                        break
                p.value = value
                p.start = text.find(p.pattern)
                p.end = p.start + len(value)
                text = text.replace(p.pattern, value, 1)

                # clear up any whitespace issues...
                text = " ".join(text.split())
        return text


class Parsers(MutableSequence):
    def __init__(self):
        super().__init__()
        self.available = []
        self.used = []
        self.important_count = 0

    def _index(self, i):
        if i < len(self.available):
            return i
        else:
            return i - len(self.available)

    def _list(self, i):
        if i < len(self.available):
            return self.available
        else:
            return self.used

    def __setitem__(self, i: int, obj) -> None:
        self._list(i)[self._index(i)] = obj

    def __delitem__(self, i: int) -> None:
        del self._list(i)[self._index(i)]

    def __getitem__(self, i):
        if isinstance(i, slice):
            return [self._list(x)[self._index(x)] for x in range(i.start, i.stop, i.step or 1)]
        return self._list(i)[self._index(i)]

    def __len__(self) -> int:
        return len(self.available) + len(self.used)

    def insert(self, index: int, obj) -> None:
        self.available.insert(index, obj)

    def get_text(self):
        """
        Pick an unused text by poping it off the top of the stack

        :return: str - The next unused text
        """
        while self.available:
            parser = self.available.pop()
            self.used.append(parser)
            yield parser

    def load(self, data, grammars=None):
        # self.domain = intent_data['domain']
        if not data:
            raise RuntimeError("Need text templates to process Intents!")

        for text in data:
            if isinstance(text, str):
                self.append(TextParser(text, grammars))

            elif isinstance(text, (OrderedDict, dict)):
                for name, value in text.items():
                    if name == 'important':
                        [self.insert(0, TextParser(x, grammars)) for x in value]
                        self.important_count += len(value)
            else:
                raise RuntimeError(f"Unknown type in 'texts' section: {text}")

    def invalidate_text(self, parser):
        if parser in self.available:
            self.available.remove(parser)
            self.used.append(parser)

    def get_used(self):
        """
        Randomly pick from the "used" list.

        :return: str - A random text
        """
        if self.used:
            return random.choice(self.used)

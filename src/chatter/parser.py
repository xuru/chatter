import copy
import logging
import random

from chatter.combinator import Combinator
from chatter.exceptions import PlaceholderError
from chatter.utils.regex import REPLACEMENT_PATTERN

PATTERN_RESERVED_CHARS = "{}>?"
PATTERN_OPTIONAL = "?"
PATTERN_PRIORITY = ">"

logger = logging.getLogger(__name__)


class TextParser:
    def __init__(self, text, grammars=None):
        self.grammars = grammars
        self.placeholders = []
        self.names = []
        self.text = copy.copy(text)
        self.combinator = None

        self.setup_placeholders()

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

    def ensure_priority_combinations(self, num: int):
        """
        Ensure that ALL possible values of priority placeholders are represented by the first `num` combinations.

        :param num: The number of combinations requested.
        :return: None
        """
        self.combinator.ensure_priorities(num)

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
        for index, name in enumerate(self.names):
            choice_index = combination[index]
            p = self.placeholders[index]
            value = grammars[name].choices[choice_index]

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

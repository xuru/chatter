import copy
import itertools
import logging
import random

from chatter.exceptions import PlaceholderError
from chatter.utils.regex import REPLACEMENT_PATTERN

logger = logging.getLogger(__name__)


class Placeholder:
    def __init__(self, text: str):
        self.placeholder_text = text.strip()
        self.optional = '?' in text
        self.ignore = False if self.optional is False else random.choice([True, False])
        self.name = text.strip('{}?')
        self.grammar = None  # could be a Grammar or Entity

    def process(self, text, excludes=None):
        return self.grammar.update(self.placeholder_text, text, excludes=excludes)

    def __repr__(self):
        rv = f"<Placeholder {self.name}>"
        if self.optional:
            rv += " optional"
        if self.ignore:
            rv += " ignored"
        return rv


def get_all_placeholder_values(text, grammars):
    original_text = copy.copy(text)
    rv = []

    placeholders = [Placeholder(text) for text in REPLACEMENT_PATTERN.findall(text)]
    grammar_values = []
    for p in placeholders:
        try:
            values = copy.copy(grammars[p.name].choices)
        except KeyError:
            raise PlaceholderError(placeholder_text=p.name)

        if p.optional:
            values.append('')
        grammar_values.append(values)

    # grammar_values = [grammars[p.name].choices for p in placeholders]

    combinations = list(itertools.product(*grammar_values))

    for options in combinations:
        text = copy.copy(original_text)
        for index, placeholder in enumerate(placeholders):
            text = text.replace(placeholder.placeholder_text, options[index])
        text = " ".join(text.split())
        rv.append(text.strip())
    return rv


def process_placeholders(text, grammars):
    for placeholder_text in REPLACEMENT_PATTERN.findall(text):
        placeholder = Placeholder(placeholder_text)
        if placeholder.ignore:
            text = text.replace(placeholder.placeholder_text, '')
        elif placeholder.name in grammars:
            value = random.choice(grammars[placeholder.name].values)
            text = text.replace(placeholder.placeholder_text, value)
        else:
            logger.warning(f"Unknown placeholder: {placeholder}")
    return text.strip()

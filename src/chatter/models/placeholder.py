import copy
import logging
import random

from chatter.utils.regex import REPLACEMENT_PATTERN

logger = logging.getLogger(__name__)


class Placeholder:
    def __init__(self, text: str):
        self.placeholder_text = text.strip()
        self.optional = False
        self.ignore = False
        self.name = text.strip('{}')
        self.grammar = None  # could be a Grammar or Entity

        # check if it is optional
        if self.name.endswith('?'):
            self.name = self.name.strip('?')
            self.optional = True
            self.ignore = random.choice([True, False])

    def process(self, text):
        self.grammar.update(self.placeholder_text, text)
        text = text.replace(self.placeholder_text, self.grammar.value)
        return text

    def __repr__(self):
        rv = f"<Placeholder {self.name}>"
        if self.optional:
            rv += " optional"
        if self.ignore:
            rv += " ignored"
        return rv


def all_placeholders(text, grammars):
    original_text = copy.copy(text)
    rv = []
    for placeholder_text in REPLACEMENT_PATTERN.findall(text):
        placeholder = Placeholder(placeholder_text)
        if placeholder.optional:
            text = original_text.replace(placeholder.placeholder_text, '')
            rv.append(text.strip())

        if placeholder.name in grammars:
            for value in grammars[placeholder.name].values:
                text = original_text.replace(placeholder.placeholder_text, value)
                rv.append(text.strip())
        else:
            logger.warning(f"Unknown placeholder: {placeholder}")
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

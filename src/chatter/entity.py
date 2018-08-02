import logging

from chatter.placeholder import get_all_placeholder_values

logger = logging.getLogger(__name__)


def process_template(template, grammars):
    values = []
    if '{' in template:
        all_values = get_all_placeholder_values(template, grammars)
        values.extend(all_values)
    else:
        values.append(template)
    return values


class Entity:
    def __init__(self, grammar, intent=None):
        self.grammar = grammar
        self.value = None
        self.entity_value = None
        self.name = grammar.name
        self.start = 0
        self.end = 0
        self.intent = intent
        self.used_synonyms = []

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.grammar.name} {self.value} {self.entity_value} {self.start} {self.end}>"

    @property
    def choices(self):
        return self.grammar.choices

    def update(self, placeholder_text: str, text: str, value: int = None):
        self.start = text.find(placeholder_text) + 1
        text = self.grammar.update(placeholder_text, text, value)
        self.end = self.start + len(self.grammar.value)
        self.value = self.grammar.value
        self.entity_value = self.grammar.entity_value
        if self.entity_value != self.value:
            self.used_synonyms.append(self.entity_value)
        return text

    def to_example(self):
        # TODO
        return dict(start=self.start, end=self.end, value=self.entity_value, entity=self.name)

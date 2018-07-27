import copy
import logging
import random
from typing import List

from chatter.entity import Entity
from chatter.placeholder import Placeholder
from chatter.utils.regex import REPLACEMENT_PATTERN

logger = logging.getLogger(__name__)


class Combinations:
    def __init__(self, data):
        self.list_of_lists = data
        self.used_keys = []

    def find_unused(self):
        combo = [random.choice(l) for l in self.list_of_lists]
        key = "".join(str(x) for x in combo)

        while key in self.used_keys:
            combo = [random.choice(l) for l in self.list_of_lists]
            key = "".join(str(x) for x in combo)
        self.used_keys.append(key)
        return combo


class CommonExample:
    def __init__(self, template, parent=None):
        self.template = template
        self.text = copy.copy(template)
        self.parent = parent
        self.entities = []
        self.grammars = []
        self.synonyms_used = {}
        self.combination: list = []
        self.picker = None
        self.grammar_values = None
        self.placeholders = []

        self.find_unused_combination()

    def all_grammars(self) -> list:
        """ To ensure we always combine them the same way. """
        return self.grammars + self.entities

    def to_dict(self) -> dict:
        return dict(
            text=self.text,
            intent=self.parent.name,
            entities=[e.to_example() for e in self.entities]
        )

    def find_unused_combination(self):
        if self.grammar_values is None:
            self.grammar_values = []
            for placeholder in self.get_placeholders():
                self.placeholders.append(placeholder)
                self.grammar_values.append(list(range(len(placeholder.grammar.choices))))

                # put it in the right list
                if placeholder.grammar.is_entity:
                    self.entities.append(Entity(placeholder.grammar))
                else:
                    self.grammars.append(placeholder.grammar)

        self.picker = Combinations(self.grammar_values)
        self.combination = self.picker.find_unused()
        self.parent.used_combinations[self.text].append(set(self.combination))

    def get_combinations(self):
        return {g.name: len(g.choices) for g in self.all_grammars()}

    def process(self):
        for index, placeholder in enumerate(self.placeholders):
            grammar = placeholder.grammar

            entities_map = {e.name: e for e in self.entities}

            if grammar.is_entity:
                entity = entities_map[grammar.name]
                self.text = entity.update(placeholder.placeholder_text, self.text, self.combination[index])
            else:
                self.text = grammar.update(placeholder.placeholder_text, self.text, self.combination[index])

            # we need to also keep track of the synonyms used...
            self.synonyms_used.update({
                name: placeholder.grammar.synonyms[name] for name in placeholder.grammar.used_synonyms
            })

    def get_placeholders(self) -> List[Placeholder]:
        rv = []
        for placeholder_text in REPLACEMENT_PATTERN.findall(self.template):
            placeholder = Placeholder(placeholder_text)
            if self.parent is not None:
                grammar = self.parent.grammars[placeholder.name]
                placeholder.grammar = grammar
            rv.append(placeholder)
        return rv

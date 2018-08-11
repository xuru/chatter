import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class CommonExample:
    def __init__(self, parent=None):
        self.parent = parent
        self.text = None

        self.entities = []
        self.grammars = []
        self.synonyms_used = defaultdict(list)
        self.combination: list = []
        self.picker = None
        self.grammar_values = None
        self.placeholders = []

    @property
    def synonyms(self):
        return {name: list(value) for name, value in self.synonyms_used.items()}

    def to_dict(self) -> dict:
        return dict(
            text=self.text,
            intent=self.parent.name,
            entities=self.entities
        )

    def process(self, parser, combination):
        self.text = parser.process(combination, self.parent.grammars)

        if combination:
            for index, name in enumerate(parser.names):
                grammar = self.parent.grammars[name]
                if grammar.is_entity:
                    placeholder = parser.placeholders[index]
                    if placeholder.synonym:
                        # instead of usng a set(), do this to preserve order
                        try:
                            if placeholder.synonym in grammar.synonyms:
                                for n in grammar.synonyms[placeholder.synonym]:
                                    if n not in self.synonyms_used[placeholder.synonym]:
                                        self.synonyms_used[placeholder.synonym].append(n)
                            elif placeholder.synonym in self.parent.grammars:
                                for n in self.parent.grammars[placeholder.synonym].choices:
                                    if n not in self.synonyms_used[placeholder.synonym]:
                                        self.synonyms_used[placeholder.synonym].append(n)
                        except Exception as err:
                            print('bob')
                    if placeholder.synonym or placeholder.value:
                        self.entities.append(
                            dict(start=placeholder.start, end=placeholder.end,
                                 value=placeholder.synonym or placeholder.value, entity=name))

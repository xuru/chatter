import copy

from chatter.models.placeholder import Placeholder
from chatter.utils.regex import REPLACEMENT_PATTERN


class CommonExample:
    def __init__(self, template, parent=None):
        self.text = template
        self.parent = parent
        self.entities = []
        self.grammars = []
        self.synonyms_used = {}

    def to_dict(self):
        return dict(
            text=self.text,
            intent=self.parent.name,
            entities=[e.to_example() for e in self.entities]
        )

    def combinations(self):
        """
        Return the number of values available for each grammar
        """
        rv = {}
        grammars = [p.grammar for p in self.get_placeholders()]

        for grammar in grammars:
            rv[grammar.name] = len(grammar.values)
        return rv

    def process(self, excludes: list=None):
        if excludes is None:
            excludes = []

        text = copy.copy(self.text)
        rv = {}
        for placeholder in self.get_placeholders():
            grammar = placeholder.grammar

            # put it in the right list
            if grammar.is_entity():
                self.entities.append(grammar)
            else:
                self.grammars.append(grammar)

            # choose an available value
            name = grammar.name
            g_excludes = excludes[name] if name in excludes else []
            value = grammar.choose(exclude=g_excludes)
            if value is None:
                raise RuntimeError(f"Ran out of choices for {grammar}")

            # update our text template
            text = placeholder.process(text)

            # remember what we choose
            rv[name] = value

            # we need to also keep track of the synonyms used...
            self.synonyms_used.update({
                name: grammar.synonyms[name] for name in grammar.used_synonyms
            })

        return rv

    def get_placeholders(self):
        rv = []
        for placeholder_text in REPLACEMENT_PATTERN.findall(self.text):
            placeholder = Placeholder(placeholder_text)
            if self.parent is not None:
                placeholder.grammar = self.parent.grammars[placeholder.name]
            rv.append(placeholder)
        return rv

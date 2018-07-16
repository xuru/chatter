import json
import random
import re
from collections import defaultdict

from chatter.models.base import IntentBase
from chatter.models.entity import Entity

REPLACEMENT_PATTERN = re.compile(r'([{].+?[}])')


class RasaNLUIntent(IntentBase):
    def __init__(self, intent_name):
        super().__init__(intent_name)
        self.grammers_indexes_used = defaultdict(set)
        self.entities_indexes_used = defaultdict(set)
        self.entities_used = []

    def _reset(self):
        self.grammers_indexes_used = defaultdict(set)
        self.entities_indexes_used = defaultdict(set)
        self.entities_used = []

    def to_json(self, num=1):
        return json.dumps(self._generate(num), indent=2)

    def _generate(self, num=1):
        examples = [self.common_example() for _ in range(num)]
        return dict(
            rasa_nlu_data=dict(
                regex_features=self.regex_features(),
                entity_synonyms=self.entity_synonyms(),
                common_examples=examples
            ))

    def common_example(self, text=None):
        if not self.templates:
            raise RuntimeError("Need text templates to process Rasa examples!")
        self._reset()

        if text is None:
            text = self.choose_text()
        text = self.process_text(text)

        common_example = dict(
            text=text,
            intent=self.name,
            entities=[e.to_dict() for e in self.entities_used])
        return common_example

    def entity_synonyms(self):
        rv = []
        for entity_name, values in self.synonyms.items():
            if isinstance(values, dict):
                for name, value in values.items():
                    rv.append(dict(value=name, synonyms=value))
            else:
                rv.append(dict(value=entity_name, synonyms=values))
        return rv

    def regex_features(self):
        return [
            dict(name="zipcode", pattern="[0-9]{5}")
        ]

    def choose_text(self) -> str:
        return random.choices(self.templates)[0]

    def get_placeholders(self, text):
        rv = {}
        for placeholder in  REPLACEMENT_PATTERN.findall(text):
            name = placeholder.strip('{}')

            # check if it's optional
            if name.endswith('?'):
                if random.randint(0, 1):
                    rv[placeholder] = None
                    continue
                else:
                    name = name.strip('?')
            rv[placeholder] = name
        return rv

    def _get_next_index(self, indexes, indexes_used):
        all_indexes = set(range(0, len(indexes)))
        available_indexes = all_indexes - indexes_used
        if not available_indexes:
            # we used all of them, so pick randomly now
            index = random.choice(list(all_indexes))
        else:
            index = random.choice(list(available_indexes))
        return index

    def process_text(self, text: str):
        for placeholder, name in self.get_placeholders(text).items():
            # if the placeholder is optional and is None, we skip it
            if name is None:
                text = text.replace(placeholder, '').strip()
                continue

            if name in self.grammers:
                text = self.process_grammer(name, placeholder, text)
            elif name in self.entities:
                text = self.process_entity(name, placeholder, text)
            else:
                raise RuntimeError(f"Unknown placeholder: {name}")
        return text

    def process_grammer(self, name, placeholder, text):
        # save off which index we used
        index = self._get_next_index(self.grammers[name], self.grammers_indexes_used[name])
        self.grammers_indexes_used[name].add(index)
        repl = self.grammers[name][index]
        return text.replace(placeholder, repl).strip()

    def process_entity(self, name, placeholder, text):
        index = self._get_next_index(self.entities[name], self.entities_indexes_used[name])
        self.entities_indexes_used[name].add(index)

        repl = self.entities[name][index]
        entity = Entity(name).update(repl, placeholder, text)
        self.entities_used.append(entity)
        return text.replace(placeholder, repl).strip()

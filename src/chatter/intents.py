import random
import json
import re

from chatter.parser import load_yaml

REPLACEMENT_PATTERN = re.compile(r'([{].+?[}])')


def loader(filename):
    intents = {}
    data = load_yaml(filename)

    # usually only one intent perfile, but could do multiple (restaurant_search)
    for intent_name, intent_data in data.items():
        intents[intent_name] = Intent(intent_name).load(intent_data)
    return intents


class Intent:
    def __init__(self, intent_name=None):
        self.name = intent_name
        self.domain = None
        self.templates = []
        self.grammers = {}
        self.entities = {}
        self.synonyms = {}

    def load(self, intent_data):
        self.domain = intent_data['domain']
        self.templates = intent_data['text']

        # Grammers
        for name, value in self.get_data(intent_data['grammers']).items():
            self.grammers[name] = value

        # entities
        entities = intent_data['entities']
        for name, value in self.get_data(entities).items():
            self.entities[name] = value

            # synonyms
            if 'synonyms' in entities and entities['synonyms']:
                self.synonyms[name] = self.get_data(entities['synonyms'])

        return self

    @staticmethod
    def get_data(data):
        rv = {}

        # only include on the first level... consider recursion at a later point
        if 'included' in data and data['included']:
            [rv.update(x) for x in data['included']]

        if 'contents' in data and data['contents']:
            rv.update(data['contents'])

        return rv

    def common_example(self):
        template = random.choices(self.templates)[-1]
        if template:
            text, entities = self._get_replacements(template)
            common_example = dict(text=text, intent=self.name, entities=entities)
            return json.dumps(common_example, indent=2)

    def sentence(self):
        template = random.choices(self.templates)[-1]
        if template:
            text, entities = self._get_replacements(template)
            return text

    def _get_replacements(self, text: str):
        entities = []
        for placeholder in REPLACEMENT_PATTERN.findall(text):
            name = placeholder.strip('{}')

            # check if it's optional
            if name.endswith('?'):
                if random.randint(0, 1):
                    text = text.replace(placeholder, '').strip()
                    continue
                else:
                    name = name.strip('?')

            if name in self.grammers:
                repl = random.choice(self.grammers[name])
            elif name in self.entities:
                repl = random.choice(self.entities[name])
                start = text.find(placeholder) + 1
                end = start + len(repl)
                entities.append(dict(start=start, end=end, value=repl, entity=name))
            else:
                raise RuntimeError(f"Unknown placeholder: {name}")

            text = text.replace(placeholder, repl).strip()

        return text, entities

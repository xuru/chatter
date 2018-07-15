

class IntentBase:
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
        for name, value in self._parse_data(intent_data['grammers']).items():
            self.grammers[name] = value

        # entities
        entities = intent_data['entities']
        for name, value in self._parse_data(entities).items():
            self.entities[name] = value

            # synonyms
            if 'synonyms' in entities and entities['synonyms']:
                self.synonyms[name] = self._parse_data(entities['synonyms'])

        return self

    @staticmethod
    def _parse_data(data):
        rv = {}

        # only include on the first level... consider recursion at a later point
        if 'included' in data and data['included']:
            [rv.update(x) for x in data['included']]

        if 'contents' in data and data['contents']:
            rv.update(data['contents'])

        return rv

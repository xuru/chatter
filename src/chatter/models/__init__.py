from chatter.models.rasa_nlu import RasaNLUIntent
from chatter.parser import load_yaml


def intents_loader(filename):
    intents = {}
    data = load_yaml(filename)

    # usually only one intent perfile, but could do multiple (restaurant_search)
    for intent_name, intent_data in data.items():
        intents[intent_name] = RasaNLUIntent(intent_name).load(intent_data)
    return intents

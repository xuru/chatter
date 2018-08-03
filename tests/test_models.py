import os

import pytest

from chatter.models import RasaNLUIntent
from chatter.loader import intents_loader

HERE = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="module")
def intent():
    intents = intents_loader(os.path.join(HERE, '..', 'examples', 'restaurant_search.yml'))
    for intent in intents.values():
        yield intent


def test_rasa_nlu_get_placeholders(intent: RasaNLUIntent):
    text = intent.templates[0]
    placeholders = intent.get_placeholders(text)
    n_placeholders = text.count('{')

    assert len(placeholders) == n_placeholders
    assert all(['?' not in key for key in placeholders.values() if key is not None])
    assert all(['{' not in key for key in placeholders.values() if key is not None])


def test_rasa_nlu_choose_text(intent: RasaNLUIntent):
    text = intent.choose_text()
    assert text in intent.templates


def test_rasa_nlu_regex_features(intent: RasaNLUIntent):
    data = intent.regex_features()
    assert isinstance(data, list)
    assert any([x['name'] == "zipcode" for x in data])


def test_rasa_nlu_entity_synonyms(intent: RasaNLUIntent):
    data = intent.entity_synonyms()
    assert isinstance(data, list)
    # make sure the list of synonyms is flattened
    assert all([list(x.keys()) == ['value', 'synonyms'] for x in data])


def test_rasa_nlu_common_example(intent: RasaNLUIntent):
    text = intent.templates[0]
    data = intent.common_example(text=text)

    assert isinstance(data, dict)
    assert len(data['entities']) == 2
    assert 'cuisine' in [x['entity'] for x in data['entities']]
    assert 'locations' in [x['entity'] for x in data['entities']]

    assert all([len(x) == 1 for x in intent.entities_indexes_used.values()])


def test_rasa_nlu_generate(intent: RasaNLUIntent):
    data = intent._generate(num=10)

    assert isinstance(data, dict)

    examples = data['rasa_nlu_data']['common_examples']
    assert len(examples) == 10
    assert all([len(example['entities']) == 1 or len(example['entities']) == 2 for example in examples])



import pytest

from chatter.entity import Entity


testdata = [
    ("{greetings}", ("howdy", "greetings", "{greetings}")),
    ('{greetings?}', ("howdy", "greetings", "{greetings?}")),
    ('Got some extra text {greetings?}', ("howdy", "greetings", "{greetings?}")),
]


@pytest.mark.parametrize("text,entity_data", testdata, ids=['required', 'optional', 'extra text'])
def test_entity(text, entity_data):
    entity_value, entity_name, placeholder = entity_data
    entity = Entity(entity_name)
    entity.update(entity_value, placeholder, text)

    assert entity.start == len(text[:text.find('{')]) + 1
    assert entity.end == len(entity_value) + entity.start
    assert entity.value == entity_value
    assert entity.entity == entity_name

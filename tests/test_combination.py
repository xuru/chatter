import os
from collections import OrderedDict
from glob import glob

import pytest

from chatter.parser import TextParser
from chatter.utils.yaml import load_yaml

HERE = os.path.abspath(os.path.dirname(__file__))

testdata = [
    ("{greetings?} {obtain} {cuisine} {proximity} {locations}?",
     "hi I would like chinese {food?} close to {New York}?"),
    ("{greetings?} I'm in {locations} and {obtain} {cuisine} {manners?}",
     "hi I'm in {New York} and I would like chinese {food?} thanks!"),
    ("{greetings} I'm hungry for some {cuisine} {manners?}",
     "hi I'm hungry for some chinese {food?} thanks!"),
    ("{greetings} I'm {large}. {obtain} {cuisine} {manners?}",
     "hi I'm {urgent} hungry. I would like chinese {food?} thanks!"),
    ("{greetings} I'm {medium}. {obtain} {cuisine} {manners?}",
     "hi I'm hungry. I would like chinese {food?} thanks!"),
    ("{greetings} I'm {small}. {obtain} {cuisine} {manners?}",
     "hi I'm somewhat hungry for. I would like chinese {food?} thanks!"),
]


def flatten_grammars(rv, data):
    if isinstance(data, list):
        for x in data:
            flatten_grammars(rv, x)
    elif isinstance(data, (dict, OrderedDict)):
        rv.update(data)
    else:
        raise RuntimeError(f"Got the wrong type! {data}")


@pytest.fixture(scope="module")
def grammars():
    rv = {}
    grammar_dir = os.path.join(HERE, 'test_data', 'grammars')
    for filename in glob(f"{grammar_dir}/*.yml"):
        flatten_grammars(rv, load_yaml(filename))
    entities_dir = os.path.join(HERE, 'test_data', 'entities')
    for filename in glob(f"{entities_dir}/*.yml"):
        flatten_grammars(rv, load_yaml(filename))
    return rv


@pytest.mark.parametrize("text,answer", testdata)
def test_combination(grammars, text, answer):
    parser = TextParser(text)
    for name in parser.names:
        assert name in grammars
        parser.set(name, grammars[name][0])

    assert parser.text == answer

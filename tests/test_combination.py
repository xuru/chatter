import os

import pytest

from chatter.loader import RasaNLULoader

HERE = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="module")
def loader():
    loader = RasaNLULoader(20)
    loader.load(os.path.join(HERE, "test_data", "restaurant_search.yml"))
    return loader


@pytest.fixture(scope="module")
def intent(loader):
    return loader.intents[-1]


def test_combination(intent):
    for p in intent.parsers:
        print(p.text)
        print(p.combinator.comb_values)

        for _ in range(p.combinator.count):
            combination = p.combinator.get()
            index = p.combinator.combination_to_index(combination)
            assert combination == p.combinator.index_to_combination(index)

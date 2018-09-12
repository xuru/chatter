import logging
import math
import operator
import random
from functools import reduce

from bitarray import bitarray

logger = logging.getLogger(__name__)


def _prod(numbers):
    return reduce(operator.mul, numbers, 1)


class Combinator:
    def __init__(self, placeholders: list):
        self.pool = []
        self.used = None
        self.count = 1
        self.placeholders = placeholders
        self.comb_values = []

        self.reset_combinations()

    def reset_combinations(self):
        """
        Rebuild the possible combinations, and make them available

        :return: None
        """
        self.count = 1
        self.comb_values = [p.index_range for p in self.placeholders]
        self.count = _prod(self.comb_values)
        self.used = bitarray(self.count)

    def combination_to_index(self, combination):
        total = 0
        for index, combo_item in enumerate(combination):
            if len(self.comb_values) > index + 1:
                combo_item = combo_item * _prod(self.comb_values[index + 1:])
            total += combo_item
        return total

    def index_to_combination(self, number):
        # for [5,2,6], the floor of 182/4*8 = 5, the floor of (182 - 5*4*8)/8 = 2, and the remainder is 6
        combination = []
        prev = None
        for index, combo_item in enumerate(self.comb_values):
            if len(self.comb_values) > index + 1:
                if prev is None:
                    prev = math.floor(number / _prod(self.comb_values[index + 1:]))
                    combination.append(prev)
                else:
                    prev = math.floor((number - (prev * _prod(self.comb_values[index:]))) / self.comb_values[index - 1])
                    combination.append(prev)
            else:
                combination.append(number - self.combination_to_index(combination))
        return combination

    def get(self):
        """
        Pick an unused combination by poping it off the top of the stack

        :return: list - The list of combination indexes
        """
        if self.used.all():
            return None

        combination = [random.randint(0, p.index_range - 1) for p in self.placeholders]
        index = self.combination_to_index(combination)

        miss_count = 0
        # index = random.randint(0, len(self.pool) - 1)
        while self.used[index] is True:
            miss_count += 1
            if miss_count > 100:
                logger.info(f"[get] missed over 100 guesses!")
                x = 0
                while self.used[x] is True:
                    x += 1
                self.used[x] = True
                combo = self.index_to_combination(x)
                logger.info(f"[get] found index: {x} {combo} {self.comb_values}")
                assert x == self.combination_to_index(combo)
                return combo

            combination = [random.randint(0, p.index_range - 1) for p in self.placeholders]
            index = self.combination_to_index(combination)
            # index = random.randint(0, len(self.pool) - 1)

        self.used[index] = True
        logger.info(f"[get] guessed index: {index} {combination} {self.comb_values}")
        assert index == self.combination_to_index(combination)
        return combination

    def get_used(self):
        """
        Randomly pick from the "used" list.

        :return: list - The list of combination indexes
        """
        if self.used.all():
            index = random.randint(0, self.count - 1)
            combo = self.index_to_combination(index)
            logger.info(f"[get_used] index: {index} {combo} {self.comb_values}")
            return combo

    def get_min_combinations(self):
        """
        Get a minimum number of combinations that have a possibility of representing most combinations

        :return: int - The minimum number of combination to get a fair representation
        """
        total = sum([p.index_range for p in self.placeholders if p.priority])
        if not total:
            return 1
        return total


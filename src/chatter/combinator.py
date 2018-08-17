import itertools
import logging
import random
from random import SystemRandom

logger = logging.getLogger(__name__)
cryptorand = SystemRandom()


class Combinator:
    def __init__(self, placeholders: list):
        self.used = []
        self.count = 1
        self.placeholders = placeholders
        self.comb_values = []

        self.reset_combinations()

    ################################################################################
    # Combinations
    ################################################################################
    def reset_combinations(self):
        """
        Rebuild the possible combinations, and make them available

        :return: None
        """
        self.comb_values = []
        self.count = 1
        for p in self.placeholders:
            self.comb_values.append(list(range(p.index_range)))
            self.count = self.count * p.index_range

    def get(self):
        """
        Pick an unused combination by poping it off the top of the stack

        :return: list - The list of combination indexes
        """
        if len(self.used) == self.count:
            return None

        miss_count = 0
        while True:
            combination = [random.randint(0, p.index_range - 1) for p in self.placeholders]
            key = tuple(combination)
            if key not in self.used:
                self.used.append(key)
                return combination
            else:
                miss_count += 1
                if miss_count >= 3:
                    for combo in itertools.product(*self.comb_values):
                        if combo not in self.used:
                            self.used.append(combo)
                            return combo

    def get_used(self):
        """
        Randomly pick from the "used" list.

        :return: list - The list of combination indexes
        """
        if self.used:
            key = random.choice(self.used)
            return list(key)

    def get_min_combinations(self):
        """
        Get a minimum number of combinations that have a possibility of representing most combinations

        :return: int - The minimum number of combination to get a fair representation
        """
        total = sum([p.index_range for p in self.placeholders if p.priority])
        if not total:
            return 1
        return total

    def ensure_priorities(self, num):
        """
        Ensure that ALL possible values of priority placeholders are represented by the first `num` combinations.

        :param num: The number of combinations requested.
        :return: None
        """
        # available_combinations = self.available
        # for priority_index, p in enumerate(self.placeholders):
        #     if p.priority:
        #
        #         existing = set([x[priority_index] for x in available_combinations[:num]])
        #         possible = set(range(p.index_range))
        #         missing = possible - existing
        #         logger.debug(f"  Missing: {missing} == {possible} - {existing}")
        #         if not missing:
        #             continue
        #
        #         move_list = []
        #         table_index = len(available_combinations) - 1
        #         while missing:
        #             if available_combinations[table_index][priority_index] in missing:
        #                 move_list.append(available_combinations[table_index])
        #                 missing.remove(available_combinations[table_index][priority_index])
        #             table_index -= 1
        #             if table_index <= 0:
        #                 raise RuntimeError(f"Unable to find all combinations of priorty grammar {p.name}")
        #
        #         for combination in move_list:
        #             logger.debug(f"Moving: {p.name}:{priority_index} - {combination}")
        #             available_combinations.insert(0, available_combinations.pop(available_combinations.index(combination)))
        #
        #         self.available = available_combinations
        pass

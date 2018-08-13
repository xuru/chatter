from chatter.parser import PATTERN_OPTIONAL, PATTERN_PRIORITY, PATTERN_RESERVED_CHARS, TextParser


class PlaceHolder:
    pattern: str = None
    optional: bool = False
    priority: bool = False
    name: str = None
    value: str = None
    synonym: str = None
    start: int = 0
    end: int = 0

    def __init__(self, pattern, value=None, synonym=None, start=0, end=0):
        self.pattern = pattern
        self.optional = PATTERN_OPTIONAL in pattern
        self.priority = PATTERN_PRIORITY in pattern
        self.name = pattern.strip(PATTERN_RESERVED_CHARS)
        self.index_range = 0
        self.value = value
        self.synonym = synonym
        self.start = start
        self.end = end

    def __repr__(self):
        return f"<PlaceHolder {self.name}: {self.value} [{self.start}, {self.end}]>"


def get_all_possible_values(text, grammars):
    parser = TextParser(text, grammars)
    return [parser.process(combination, grammars) for combination in parser.combinator.get()]

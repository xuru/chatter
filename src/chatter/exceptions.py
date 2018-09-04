
class CombinationsExceededError(Exception):
    pass


class GrammarError(Exception):
    pass


class PlaceholderError(Exception):
    filename: str = None
    placeholder_text: str = None
    grammar_name: str = None

    def __init__(self, *args, placeholder_text=None, filename=None, grammar_name=None, **kwargs):
        self.grammar_name = grammar_name
        self.placeholder_text = placeholder_text
        self.filename = filename
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"Unable to find grammar for {self.grammar_name}/{self.placeholder_text} in filename: {self.filename}"

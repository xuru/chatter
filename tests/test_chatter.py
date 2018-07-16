
from click.testing import CliRunner

from chatter.cli import cli


def test_main():
    runner = CliRunner()
    result = runner.invoke(cli, [])

    assert result.output.startswith('Usage:')
    assert result.exit_code == 0


def test_generate():
    runner = CliRunner()
    result = runner.invoke(cli, ['generate', 'rasa', 'nlu', '--num=10', 'examples/restaurant_search.yml'])

    assert result.output.startswith('Generating RASA NLU data for examples/restaurant_search.yml')
    assert 'restaurant_search.json' in result.output
    assert result.exit_code == 0

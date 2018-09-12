import click
from click import secho

from chatter.loader import RasaNLULoader


@click.group()
@click.pass_context
def generate(ctx):
    pass


@generate.group('rasa')
@click.pass_context
def rasa_group(ctx):
    pass


@generate.command('sentences')
@click.argument('filename', type=click.Path(exists=True))
@click.argument('outfile', default='sentences.txt', type=click.Path(exists=False))
@click.option('--num', default=0)
def load_sentences(filename, outfile, num):
    click.secho(f"Generating sentences for {filename}", fg='green')

    loader = RasaNLULoader(num)
    click.secho(f"Loading...", fg='green')
    loader.load(filename)

    for intent in loader.intents:
        secho(f"  Generating sentences...\n", fg="green")
        with open(outfile, 'w') as fp:
            with click.progressbar(intent.training_examples, label="Generating...") as bar:
                for example in bar:
                    fp.write(example.text + "\n")


@rasa_group.command('nlu')
@click.argument('filename', type=click.Path(exists=True))
@click.argument('outdir', default='results', type=click.Path(dir_okay=True))
@click.argument('testdir', default='tests/test_data', type=click.Path(dir_okay=True))
@click.option('--num', default=0)
@click.option('--test-ratio', default=20)
def load_nlu(filename, outdir, testdir, num, test_ratio):
    click.secho(f"Generating RASA NLU data for {filename}", fg='green')

    loader = RasaNLULoader(num, test_ratio)
    click.secho(f"Loading...", fg='green')
    loader.load(filename)

    click.secho(f"Saving training data", fg='green')
    loader.save(outdir)
    click.secho(f"Saving testing data", fg='green')
    loader.save_tests(testdir)

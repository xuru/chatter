import os

import click
from click import secho
from tabulate import tabulate

from chatter.models.rasa_nlu import intents_loader


@click.group()
@click.pass_context
def generate(ctx):
    pass


@generate.group('rasa')
@click.pass_context
def rasa_group(ctx):
    pass


@rasa_group.command('nlu')
@click.argument('filename', type=click.Path(exists=True))
@click.argument('outdir', default='results', type=click.Path(dir_okay=True))
@click.option('--num', default=1)
def load_file(filename, outdir, num):
    click.secho(f"Generating RASA NLU data for {filename}", fg='green')

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outdir = os.path.abspath(outdir)

    intents = intents_loader(filename)

    for intent in intents.values():
        try:
            intent.validate_num(num)
        except RuntimeError as error:
            data = [(combos, text) for text, combos in intent.get_possible_combinations().items()]
            secho(tabulate(data, headers=["Combinations", "Text template"]), fg="cyan")
            secho("")

            raise click.BadOptionUsage(str(error)) from error

        filename = os.path.join(outdir, intent.name + ".json")
        secho(f"  Generating: {filename}\n", fg="green")
        with open(filename, 'w+') as fp:
            text = intent.to_json(num)
            secho(text, fg="green")
            fp.write(text)

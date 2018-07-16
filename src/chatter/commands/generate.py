import os

import click
from click import secho

from chatter.models import intents_loader


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
        filename = os.path.join(outdir, intent.name + ".json")
        secho(f"  Generating: {filename}", fg="green")
        with open(filename, 'w+') as fp:
            fp.write(intent.to_json(num))

import os
import shutil

import click
from click import secho
from tabulate import tabulate

from chatter.loader import intents_loader, process_file, process_from_dir


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
@click.option('--num', default=1)
def load_sentences(filename, num):
    click.secho(f"Generating sentences for {filename}", fg='green')

    for intent in intents_loader(filename).values():
        try:
            intent.validate_num(num)
        except RuntimeError as error:
            data = [(combinations, text) for text, combinations in intent.get_possible_combinations().items()]
            secho(tabulate(data, headers=["Combinations", "Text template"]), fg="cyan")
            secho("")
            raise click.BadOptionUsage(str(error)) from error

        secho(f"  Generating sentences...\n", fg="green")
        for text in intent.sentences(num):
            secho(text, fg="cyan")


@rasa_group.command('nlu')
@click.argument('filename', type=click.Path(exists=True))
@click.argument('outdir', default='results', type=click.Path(dir_okay=True))
@click.option('--num', default=0)
def load_nlu(filename, outdir, num):
    click.secho(f"Generating RASA NLU data for {filename}", fg='green')

    outdir = os.path.abspath(outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    else:
        shutil.rmtree(outdir, ignore_errors=False)
        os.makedirs(outdir)

    if os.path.isdir(filename):
        process_from_dir(filename, outdir, num)
    else:
        process_file(filename, outdir, num)

import os
import shutil
from collections import defaultdict

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
@click.argument('outfile', default='sentences.txt', type=click.Path(exists=False))
@click.option('--num', default=0)
def load_sentences(filename, outfile, num):
    click.secho(f"Generating sentences for {filename}", fg='green')

    for intent in intents_loader(filename).values():
        try:
            intent.validate_num(num)
        except RuntimeError as error:
            data = [(combinations, text) for text, combinations in intent.get_possible_combinations().items()]
            secho(tabulate(data, headers=["Combinations", "Text template"]), fg="cyan")
            secho("")
            raise click.BadOptionUsage(str(error)) from error

        if num == 0:
            total = intent.get_total_possible_combinations()
        else:
            total = num

        combinations = defaultdict(set)
        with click.progressbar(intent.get_combinations(num),
                               label="Calculating combinations...",
                               length=total) as bar:
            for text, seq in bar:
                combinations[text].add(seq)

        secho(f"  Generating sentences...\n", fg="green")
        with open(outfile, 'w') as fp:
            with click.progressbar(intent.sentences(num, combinations),
                                   label="Generating...",
                                   length=total) as bar:
                for text in bar:
                    fp.write(text + "\n")


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

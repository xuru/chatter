import os

import click
from click import secho
from tabulate import tabulate

from chatter.rasa_nlu import intents_loader


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

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outdir = os.path.abspath(outdir)

    if os.path.isdir(filename):
        load_from_dir(filename, outdir, num)
    else:
        load_file(filename, outdir, num)


def load_file(filename, outdir, num):
    for intent in intents_loader(filename).values():
        filename = os.path.join(outdir, intent.name + ".json")
        secho(f"  Generating: {filename}\n", fg="green")
        data = intent.to_json(num)
        with open(filename, 'w') as fp:
            fp.write(data)
        secho(data, fg="cyan")


def load_from_dir(dirname, outdir, num):
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(dirname):
        # TODO: For now skip these specific directories, but this should be gleaned from the includes in the yml files
        if os.path.basename(root) in ['grammars', 'entities']:
            continue

        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                load_file(os.path.join(root, file), outdir, num)

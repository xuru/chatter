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
@click.option('--num', default=1)
def load_file(filename, num):
    click.secho("Filename: {}".format(filename), fg='green')
    intents = intents_loader(filename)

    for intent in intents.values():
        secho(f"Intent: {intent.name}", fg="cyan")
        secho(intent.generate(num), fg="green")

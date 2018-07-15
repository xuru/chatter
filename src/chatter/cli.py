"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mchatter` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``chatter.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``chatter.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import os
import click

from chatter.commands.generate import generate

here = os.path.abspath(os.path.dirname(__file__))


@click.group()
@click.option('--verbose', '-v', count=True, help="The verbosity of the output")
@click.pass_context
def cli(ctx, verbose):
    if not hasattr(ctx, 'obj') or (hasattr(ctx, 'obj') and ctx.obj is None):
        ctx.obj = {}
    ctx.obj['verbosity'] = verbose


cli.add_command(generate)

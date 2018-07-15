import contextlib
import os

import yaml


def _include_yaml(loader, node):
    """Load another YAML file and embeds it using the !include tag.
    Example:
        device_tracker: !include device_tracker.yaml
    """
    fname = os.path.join(os.path.dirname(loader.name), node.value)
    with open(fname) as fp:
        return yaml.load(fp.read(), yaml.SafeLoader)


yaml.SafeLoader.add_constructor('!include', _include_yaml)


@contextlib.contextmanager
def remember_cwd():
    _curdir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(_curdir)


def load_yaml(filename):
    with open(filename) as fp:
        with remember_cwd():
            os.chdir(os.path.abspath(os.path.dirname(filename)))
            return yaml.load(fp.read(), yaml.SafeLoader)

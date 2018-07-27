import contextlib
import json
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


def load_yaml(stream):
    if hasattr(stream, 'read'):
        fp = stream
    elif isinstance(stream, (str, bytes)):
        fp = open(stream, 'r')
    else:
        raise RuntimeError("Stream must be a filename, or a file object")

    try:
        with remember_cwd():
            os.chdir(os.path.abspath(os.path.dirname(fp.name)))
            data = yaml.load(fp.read(), yaml.SafeLoader)
    finally:
        fp.close()
    return data



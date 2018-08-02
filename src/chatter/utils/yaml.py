import os
from collections import OrderedDict

import yaml


class YamlLoader(yaml.SafeLoader):

    def __init__(self, stream):
        self._root = os.path.dirname(stream.name)
        super().__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, YamlLoader)


def _ordered_dict(loader, node):
    """Load YAML mappings into an ordered dict to preserve key order."""
    loader.flatten_mapping(node)
    return OrderedDict(loader.construct_pairs(node))


YamlLoader.add_constructor('!include', YamlLoader.include)
YamlLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _ordered_dict)


def load_yaml(stream):
    with open(stream, 'r') as fp:
        data = list(yaml.load_all(fp, YamlLoader))
    return data



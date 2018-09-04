import copy
import logging
import os
from glob import glob
from typing import Dict

from chatter.exceptions import PlaceholderError, GrammarError
from chatter.rasa_nlu import RasaNLUIntent
from chatter.utils.yaml import load_yaml

logger = logging.getLogger(__name__)


class RasaNLULoader:

    def __init__(self, num=1, test_ratio=0):
        self.num = num
        self.replace_existing = True
        self.clean_directory = True
        self.test_ratio = test_ratio
        self.intents = []

    def _ensure_outdir(self, dirname):
        dirname = os.path.abspath(dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if self.clean_directory:
            for filename in glob(os.path.join(dirname, "*.json")):
                os.remove(filename)

    def save(self, outdir, testing=False):
        self._ensure_outdir(outdir)

        for intent in self.intents:
            filename = os.path.join(outdir, intent.name + ".json")

            data = intent.json(test=testing)

            if self.replace_existing is False and os.path.exists(filename):
                logger.info(f"Skipping {filename}...")
            else:
                orig_filename = copy.copy(filename)
                index = 1
                while os.path.exists(filename):
                    basename, ext = os.path.splitext(orig_filename)
                    filename = "".join([basename, str(index), ext])
                    index += 1

                logger.info(f"Generating: {filename}")
                with open(filename, 'w') as fp:
                    fp.write(data)

    def save_tests(self, outdir):
        self.save(outdir, testing=True)

    def load(self, path, replace_existing=True):
        self.replace_existing = replace_existing

        if os.path.isdir(path):
            self.load_from_dir(path)
        else:
            self.load_file(path)
        return self.intents

    def load_file(self, filename):
        data_set = load_yaml(filename)

        # usually only one intent per file, but can do multiple
        for data in data_set:
            for intent_name, intent_data in data.items():
                try:
                    intent = RasaNLUIntent(intent_name).load(intent_data)
                    intent.process(self.num, self.test_ratio)
                    self.intents.append(intent)
                except PlaceholderError as err:
                    err.filename = filename
                    logger.error(f"{err}. Ensure that the grammar is defined or included.")
                except GrammarError as err:
                    raise GrammarError(f"Error in file {filename}: {err}")

    def load_from_dir(self, dirname):
        # traverse root directory, and list directories as dirs and files as files
        for root, dirs, files in os.walk(dirname):
            # TODO: For now skip these specific directories,
            # but this should be gleaned from the includes in the yml files
            if os.path.basename(root) in ['grammars', 'entities']:
                continue

            for file in files:
                if file.endswith('.yml') or file.endswith('.yaml'):
                    self.load_file(os.path.join(root, file))

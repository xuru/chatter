import copy
import logging
import os
from chatter.rasa_nlu import RasaNLUIntent
from chatter.utils.yaml import load_yaml

logger = logging.getLogger(__name__)


def intents_loader(stream):
    intents = {}
    data_set = load_yaml(stream)

    # usually only one intent perfile, but can do multiple
    for data in data_set:
        for intent_name, intent_data in data.items():
            intents[intent_name] = RasaNLUIntent(intent_name).load(intent_data)
    return intents


def process_file(filename, outdir, num, skip_existing=False):
    for intent in intents_loader(filename).values():
        filename = os.path.join(outdir, intent.name + ".json")
        data = intent.to_json(num)

        if skip_existing and os.path.exists(filename):
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


def process_from_dir(dirname, outdir, num, skip_existing=False):
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(dirname):
        # TODO: For now skip these specific directories, but this should be gleaned from the includes in the yml files
        if os.path.basename(root) in ['grammars', 'entities']:
            continue

        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                process_file(os.path.join(root, file), outdir, num, skip_existing)

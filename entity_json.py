"""
Convert @@tagged_entities##
Into JSON format
Identifies: sample ID, entity position (index), text type (title/abstract), tagged_entity, entity label
"""


import re
import json
import os
from pathlib import Path


json_entries = {}


def build_entry(title, abstract, pmid, entities):
    title = re.sub('(@@|##)', '', title)  # remove instance tags
    abstract = re.sub('(@@|##)', '', abstract)  # remove instance tags

    global json_entries
    json_entries[pmid] = {
            "metadata": {
                "title": title,
                "abstract": abstract
            },
            "entities": entities
        }


def format_entity_entry(dictionary, instance, pmid, location, label, start, end, offset):
    entity = instance[start+2:end]  # skip @@

    start_adjusted = start - offset  # not counting first @
    end_adjusted = start_adjusted + len(entity) - 1  # not counting @@
    idx = int(pmid)+start_adjusted

    dictionary[idx] = {
        "start_idx": start_adjusted,
        "end_idx": end_adjusted,
        "location": location,
        "entity": entity,
        "label": label
    }


def search_samples(pmid_entries, string, pmid, location, label):
    i = 0
    offset = 0

    while i < len(string) - 1:
        if string[i:i + 2] == "@@":
            start_index = i
            i += 2

            end_index = string.find("##", i)
            if end_index == -1: # incorrect tag
                break
            format_entity_entry(pmid_entries, string, pmid, location, label, start_index, end_index, offset)

            # offset adjusts count for next set of tags
            offset += 4  # @@ and ##
            i = end_index + 2 # skip ##
        else:
            i += 1


def extract_entities(file):
    entries = {}

    print(file)
    with open(file, 'r') as entity_file:
        file_str = str(file)
        pmid = re.search('/([0-9]*)_tagged.json', file_str).group(1)
        label = re.search('/(.*)/', file_str).group(1)
        text = entity_file.read()

        # title, abstract
        match = re.search(r'"tagged_title":\s*"([^"]+)",\s*"tagged_abstract":\s*"([^"]+)"', text, re.DOTALL)

        title = match.group(1)
        search_samples(entries, title, pmid, 'title', label)

        abstract = match.group(2)
        search_samples(entries, abstract, pmid, 'abstract', label)

        build_entry(title, abstract, pmid, entries)


def walk_directory(tagged_output):
    # parent directory
    for root, _, files in os.walk(tagged_output):
        # entity files
        for file in files:
            # samples
            if file.endswith('_tagged.json'):
                sample_path = Path(os.path.join(root, file))
                extract_entities(sample_path)


if __name__ == '__main__':
    entity_folder_name = 'Data'

    walk_directory(entity_folder_name)
    
    with open('entity_indices.json', 'w') as json_file:
        json.dump(json_entries, json_file, indent=4)
from sys import argv
import json

global json_file


# entities w multiple meanings?
def missing_whole_entity(tagged_entities):
    incorrect_entities = []
    # find all entities with a tagged sub-entity
    for i in range(len(tagged_entities)):
        for k in range(len(tagged_entities)):
            if i == k:  # same entity
                continue

            idx, entity, label, s, e, text = tagged_entities[i]
            idx2, entity2, label2, s2, e2, text2 = tagged_entities[k]

            if entity == entity2:  # same entity string, different entities
                if label != label2:
                    incorrect_entities.append([idx2, s2, e2, entity2, label])  # arbitrarily choose entity1 label
                continue

            if entity2 in entity:  # entity2 is possibly missing whole entity
                subentity_length = e2 - s2
                added_range = e - s - subentity_length + 1  # possible range for whole entity

                possible_start_index = max(0, s2 - added_range)
                possible_end_index = min(len(text2), e2 + added_range + 1)

                spliced_text = text2[possible_start_index:possible_end_index]

                if spliced_text.find(entity) != -1:  # the parent entity is found
                    start_index = spliced_text.find(entity) - spliced_text.find(entity2) + s2
                    end_index = start_index + len(entity) - 1

                    incorrect_entities.append([idx2, start_index, end_index, entity, entity2, label])

    return incorrect_entities


def extract(json_entry):
    title = json_entry["metadata"]["title"]
    abstract = json_entry["metadata"]["abstract"]
    entity_labels = []

    for idx, entity in json_entry["entities"].items():
        tagged_entity = entity["entity"]
        label = entity["label"]
        location = entity["location"]
        s_idx = entity["start_idx"]
        e_idx = entity["end_idx"]

        if location == 'title':
            entity_labels.append([idx, tagged_entity, label, s_idx, e_idx, title])
        elif location == 'abstract':
            entity_labels.append([idx, tagged_entity, label, s_idx, e_idx, abstract])


    return missing_whole_entity(entity_labels)


def read_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)


if __name__ == '__main__':
    json_file = argv[1]
    json_dict = read_json(json_file)

    for pmid, entry in json_dict.items():
        fixes = extract(entry)
        print(fixes)

        for idx, start_index, end_index, entity, _, label in fixes:
            json_dict[pmid]["entities"][idx]["entity"] = entity
            json_dict[pmid]["entities"][idx]["start_idx"] = start_index
            json_dict[pmid]["entities"][idx]["end_idx"] = end_index
            json_dict[pmid]["entities"][idx]["label"] = label

    with open('entity_indices_clean.json', 'w') as f:
        json.dump(json_dict, f, indent=2)

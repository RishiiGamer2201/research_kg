"""
DBP-5L-Ind Preprocessor for BGE-M3 Training
Converts the entity-disjoint inductive splits into JSON format for training.
Also creates the relation-indexed anchor dictionary needed for fast RAA sampling.

Usage:
    python3 preprocess_dbp5l_ind.py

Output:
    ~/research_kg/DBP5L/processed/
        train.json          -- training examples
        valid.json          -- validation examples
        test.json           -- test (inductive) examples
        entities.json       -- entity_id -> display_name mapping
        anchors_by_rel.json -- relation_id -> [list of (h,t) pairs] for RAA sampling
"""

import os
import json
from collections import defaultdict

IND = os.path.expanduser('~/research_kg/DBP5L/ind')
RAW = os.path.expanduser('~/research_kg/DBP5L/raw')
OUT = os.path.expanduser('~/research_kg/DBP5L/processed')
LANGS = ['en', 'fr', 'es', 'ja', 'el']

os.makedirs(OUT, exist_ok=True)


def load_triples(path):
    triples = []
    if not os.path.exists(path):
        return triples
    with open(path) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                triples.append((int(parts[0]), int(parts[1]), int(parts[2])))
    return triples


def load_entity_uris(path):
    """Returns dict: entity_id (int) -> URI string"""
    entities = {}
    with open(path) as f:
        for i, line in enumerate(f):
            uri = line.strip()
            name = uri.split('/')[-1].replace('_', ' ')
            entities[i] = {'uri': uri, 'name': name}
    return entities


def uri_to_name(uri):
    """Convert DBpedia URI to a readable name."""
    name = uri.split('/')[-1]
    name = name.replace('_', ' ')
    # Handle URL encoding
    try:
        from urllib.parse import unquote
        name = unquote(name)
    except Exception:
        pass
    return name


# Step 1: Build entity ID mapping across all languages
# Entity IDs in each language file are local (0-indexed per language)
# We make them global: global_id = (lang_offset + local_id)
print('=== Step 1: Building entity mapping ===')
lang_offsets = {}
offset = 0
all_entities = {}  # global_entity_id -> {lang, local_id, name, uri}

for lang in LANGS:
    uri_path = f'{IND}/{lang}/entity_uris.txt'
    if not os.path.exists(uri_path):
        print(f'  [WARN] Missing {uri_path}')
        continue
    local_entities = load_entity_uris(uri_path)
    lang_offsets[lang] = offset
    for local_id, info in local_entities.items():
        global_id = offset + local_id
        all_entities[global_id] = {
            'lang': lang,
            'local_id': local_id,
            'global_id': global_id,
            'name': uri_to_name(info['uri']),
            'uri': info['uri'],
            # Description: use name as placeholder; can be enriched with Wikipedia API later
            'description': uri_to_name(info['uri']),
        }
    offset += len(local_entities)
    print(f'  {lang.upper()}: {len(local_entities)} entities (offset {lang_offsets[lang]})')

print(f'  Total global entities: {len(all_entities)}')

# Save entity index
with open(f'{OUT}/entities.json', 'w', encoding='utf-8') as f:
    json.dump(all_entities, f, ensure_ascii=False, indent=2)
print(f'  Saved entities.json')


# Step 2: Build global triple lists per split
print('\n=== Step 2: Building global triple lists ===')

train_examples = []
valid_examples = []
test_examples = []

# Per-relation index for RAA anchor sampling (KEY FIX: dict instead of O(N^2) scan)
anchors_by_rel = defaultdict(list)  # relation_id -> [(h_global, t_global, lang), ...]

for lang in LANGS:
    if lang not in lang_offsets:
        continue
    off = lang_offsets[lang]

    def to_global(local_id):
        return off + local_id

    def make_example(h, r, t, split, lang):
        return {
            'h': to_global(h),
            'r': int(r),
            't': to_global(t),
            'h_name': all_entities.get(to_global(h), {}).get('name', str(h)),
            't_name': all_entities.get(to_global(t), {}).get('name', str(t)),
            'h_desc': all_entities.get(to_global(h), {}).get('description', ''),
            't_desc': all_entities.get(to_global(t), {}).get('description', ''),
            'lang': lang,
            'split': split,
        }

    # Train triples
    triples = load_triples(f'{IND}/{lang}/train.txt')
    for h, r, t in triples:
        ex = make_example(h, r, t, 'train', lang)
        train_examples.append(ex)
        # Index for RAA anchors: only train triples are used as anchors during training
        anchors_by_rel[r].append({'h': to_global(h), 't': to_global(t), 'lang': lang})

    # Valid triples
    triples = load_triples(f'{IND}/{lang}/valid.txt')
    for h, r, t in triples:
        valid_examples.append(make_example(h, r, t, 'valid', lang))

    # Test triples (inductive: unseen entities)
    triples = load_triples(f'{IND}/{lang}/test.txt')
    for h, r, t in triples:
        test_examples.append(make_example(h, r, t, 'test', lang))

    print(f'  {lang.upper()}: {len(load_triples(IND+"/"+lang+"/train.txt"))} train, {len(load_triples(IND+"/"+lang+"/valid.txt"))} valid, {len(load_triples(IND+"/"+lang+"/test.txt"))} test')


# Step 3: Save processed files
print(f'\n=== Step 3: Saving processed files ===')

with open(f'{OUT}/train.json', 'w', encoding='utf-8') as f:
    for ex in train_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')
print(f'  train.json: {len(train_examples)} examples')

with open(f'{OUT}/valid.json', 'w', encoding='utf-8') as f:
    for ex in valid_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')
print(f'  valid.json: {len(valid_examples)} examples')

with open(f'{OUT}/test.json', 'w', encoding='utf-8') as f:
    for ex in test_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')
print(f'  test.json: {len(test_examples)} examples')

# Save RAA anchor index (KEY: O(1) lookup by relation vs O(N) scan)
with open(f'{OUT}/anchors_by_rel.json', 'w', encoding='utf-8') as f:
    json.dump(dict(anchors_by_rel), f, ensure_ascii=False)
print(f'  anchors_by_rel.json: {len(anchors_by_rel)} relations indexed')


# Step 4: Save alignment links in processed format
print('\n=== Step 4: Processing alignment links ===')
align_dir = f'{IND}/align'
align_all = []
for fname in os.listdir(align_dir):
    if not fname.endswith('.tsv'):
        continue
    parts = fname.replace('.tsv', '').split('-')
    if len(parts) != 2:
        continue
    lang1, lang2 = parts
    if lang1 not in lang_offsets or lang2 not in lang_offsets:
        continue
    off1, off2 = lang_offsets[lang1], lang_offsets[lang2]
    with open(f'{align_dir}/{fname}') as f:
        for line in f:
            cols = line.strip().split()
            if len(cols) >= 2:
                try:
                    e1 = off1 + int(float(cols[0]))
                    e2 = off2 + int(float(cols[1]))
                    align_all.append({'e1': e1, 'lang1': lang1, 'e2': e2, 'lang2': lang2})
                except ValueError:
                    pass

with open(f'{OUT}/alignments.json', 'w') as f:
    json.dump(align_all, f)
print(f'  alignments.json: {len(align_all)} cross-lingual entity pairs')

# Build reverse alignment index: global_entity_id -> {lang: global_entity_id}
align_index = defaultdict(dict)
for pair in align_all:
    align_index[pair['e1']][pair['lang2']] = pair['e2']
    align_index[pair['e2']][pair['lang1']] = pair['e1']

with open(f'{OUT}/align_index.json', 'w') as f:
    json.dump(dict(align_index), f)
print(f'  align_index.json: {len(align_index)} entities with cross-lingual links')

print('\n=== DONE ===')
print(f'Processed data at: {OUT}')
print(f'Files: entities.json, train.json, valid.json, test.json')
print(f'       anchors_by_rel.json, alignments.json, align_index.json')

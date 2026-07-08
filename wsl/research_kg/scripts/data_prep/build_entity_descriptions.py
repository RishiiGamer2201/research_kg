"""
build_entity_descriptions.py
============================
Builds rich entity descriptions from KG neighborhood for DBP-5L-Ind.

Since DBP-5L has no Wikipedia abstracts, we use the training graph structure:
  entity_text = "name | relation1: neighbor1, neighbor2 | relation2: neighbor3"

This is the standard SimKGC approach — proven to dramatically improve
text-encoder KGC when descriptions are absent.

Run BEFORE training:
    python3 build_entity_descriptions.py

Output: ~/research_kg/DBP5L/processed/entity_descriptions.json
        {global_id: "name | rel1: n1, n2 | rel2: n3, n4", ...}
Then update train/valid/test preprocessing to use these descriptions.
"""
import json
import os
from collections import defaultdict

PROCESSED = os.path.expanduser('~/research_kg/DBP5L/processed')

print('Loading entities...')
with open(f'{PROCESSED}/entities.json') as f:
    entities = json.load(f)  # str(global_id) -> {name, lang, ...}

# Build name lookup
id_to_name = {int(k): v.get('name', '') for k, v in entities.items()}

print('Loading relation names...')
# Try to load relation names if available
rel_names = {}
rel_path = f'{PROCESSED}/relations.json'
if os.path.exists(rel_path):
    with open(rel_path) as f:
        rel_data = json.load(f)
    for k, v in rel_data.items():
        if isinstance(v, dict):
            name = v.get('name', v.get('uri', str(k)))
        else:
            name = str(v)
        # Clean DBpedia URI to readable name
        name = name.split('/')[-1].split('#')[-1]
        name = name.replace('_', ' ').replace('wikiPageWikiLink', 'related to')
        rel_names[int(k)] = name
else:
    print('  No relations.json found — will use relation IDs')

print('Loading all triples (train + valid)...')
all_triples = []
for split in ['train', 'valid']:
    path = f'{PROCESSED}/{split}.json'
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                all_triples.append(json.loads(line))
print(f'  Loaded {len(all_triples)} triples')

# Build neighbor lookup: entity_id -> [(relation_id, tail_id, direction), ...]
print('Building neighbor index...')
head_neighbors = defaultdict(list)   # head -> [(rel, tail)]
tail_neighbors = defaultdict(list)   # tail -> [(rel, head)]  (inverse)

for t in all_triples:
    h, r, tail = t['h'], t['r'], t['t']
    head_neighbors[h].append((r, tail))
    tail_neighbors[tail].append((r, h))

print(f'  {len(head_neighbors)} entities have outgoing edges')
print(f'  {len(tail_neighbors)} entities have incoming edges')

# Build text description for each entity
print('Building entity descriptions...')
descriptions = {}
stats = {'with_neighbors': 0, 'name_only': 0, 'no_name': 0}

for eid_str, info in entities.items():
    eid = int(eid_str)
    name = info.get('name', '')
    if not name:
        descriptions[eid] = f'entity_{eid}'
        stats['no_name'] += 1
        continue

    # Collect outgoing relations (head_entity -[rel]-> neighbors)
    out_rels = defaultdict(list)
    for (r, t) in head_neighbors.get(eid, [])[:20]:  # cap at 20 neighbors
        r_name = rel_names.get(r, f'rel_{r}')
        t_name = id_to_name.get(t, f'entity_{t}')
        if t_name and t_name != name:  # skip self-loops
            out_rels[r_name].append(t_name)

    # Collect incoming relations (neighbors -[rel]-> this entity)
    in_rels = defaultdict(list)
    for (r, h) in tail_neighbors.get(eid, [])[:10]:  # cap at 10 inverse
        r_name = rel_names.get(r, f'rel_{r}')
        h_name = id_to_name.get(h, f'entity_{h}')
        if h_name and h_name != name:
            in_rels[f'is {r_name} of'].append(h_name)

    if out_rels or in_rels:
        # Build description: "name | rel1: n1, n2 | rel2: n3"
        parts = [name]
        for r_name, neighbors in list(out_rels.items())[:5]:  # top 5 relations
            parts.append(f'{r_name}: {", ".join(neighbors[:4])}')  # top 4 per rel
        for r_name, neighbors in list(in_rels.items())[:2]:  # top 2 inverse
            parts.append(f'{r_name}: {", ".join(neighbors[:3])}')
        descriptions[eid] = ' | '.join(parts)
        stats['with_neighbors'] += 1
    else:
        # Entity appears only in test/valid set — use name only
        descriptions[eid] = name
        stats['name_only'] += 1

print(f'\nDescription stats:')
print(f'  With KG neighbors:  {stats["with_neighbors"]:,}')
print(f'  Name only (unseen): {stats["name_only"]:,}')
print(f'  No name:            {stats["no_name"]:,}')

# Show samples
print('\nSample descriptions:')
langs = ['en', 'fr', 'es', 'ja', 'el']
shown = {l: 0 for l in langs}
for eid_str, info in entities.items():
    lang = info.get('lang', 'en')
    if lang in shown and shown[lang] < 1:
        eid = int(eid_str)
        desc = descriptions.get(eid, 'MISSING')
        if len(desc) > 20 and '|' in desc:  # only show ones with neighbors
            print(f'  [{lang.upper()}] {desc[:150]}')
            shown[lang] += 1

# Save
out_path = f'{PROCESSED}/entity_descriptions.json'
# Save as int-keyed dict
save_data = {str(k): v for k, v in descriptions.items()}
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(save_data, f, ensure_ascii=False, indent=None)
print(f'\nSaved {len(descriptions):,} descriptions to {out_path}')
print(f'File size: {os.path.getsize(out_path) / 1e6:.1f} MB')

# Also clear the token cache so next training uses new descriptions
import glob
cache_files = glob.glob(os.path.expanduser('~/research_kg/DBP5L/token_cache/*.pt'))
if cache_files:
    print(f'\nNOTE: Delete token cache before retraining:')
    print(f'  rm ~/research_kg/DBP5L/token_cache/*.pt')
    print(f'  (cache has {len(cache_files)} files with old name-only descriptions)')

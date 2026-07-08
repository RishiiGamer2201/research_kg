"""
build_relation_names.py — Extract human-readable relation names from relations.txt
"""
import json
import os

PROCESSED = os.path.expanduser('~/research_kg/DBP5L/processed')
RAW = os.path.expanduser('~/research_kg/DBP5L/raw')

# Read relation URIs (index = relation ID)
rel_uris = []
with open(f'{RAW}/relations.txt') as f:
    for line in f:
        rel_uris.append(line.strip())

print(f'Loaded {len(rel_uris)} relation URIs')

# Convert URI to human-readable name
def uri_to_name(uri):
    name = uri.split('/')[-1].split('#')[-1]
    # camelCase -> words: "nfcChampion" -> "nfc champion"
    import re
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
    name = name.replace('_', ' ').lower().strip()
    return name

rel_names = {}
for i, uri in enumerate(rel_uris):
    rel_names[i] = uri_to_name(uri)

# Show samples
print('Sample relation names:')
for i in [0, 1, 2, 50, 100, 200, 358, 640]:
    if i < len(rel_names):
        print(f'  rel_{i}: {rel_names[i]}')

# Save
out_path = f'{PROCESSED}/relation_names.json'
with open(out_path, 'w') as f:
    json.dump({str(k): v for k, v in rel_names.items()}, f, indent=None)
print(f'\nSaved {len(rel_names)} relation names to {out_path}')

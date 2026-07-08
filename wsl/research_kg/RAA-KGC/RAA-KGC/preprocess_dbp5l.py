"""
Preprocess DBP-5L (KEnS format) into RAA-KGC JSON format.

Input  (KEnS):
  data/entity/{lang}.tsv   — one DBpedia URI per line; line index = entity ID
  data/kg/{lang}-train.tsv — head_idx\trel_idx\ttail_idx
  data/kg/{lang}-val.tsv
  data/kg/{lang}-test.tsv
  data/relations.txt        — one relation URI per line; line index = rel ID

Output (RAA-KGC), written to --out-dir:
  train.txt.json, valid.txt.json, test.txt.json, entities.json
"""

import argparse
import json
import os
import re
from typing import Dict, List, Tuple

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--kens-dir', default=os.path.expanduser('~/research_kg/KEnS/data'),
                    help='Path to KEnS data/ directory')
parser.add_argument('--langs', default='en,fr,es,ja,el',
                    help='Comma-separated languages to include')
parser.add_argument('--out-dir', default='data/DBP5L',
                    help='Output directory for JSON files')
args = parser.parse_args()

LANGS = args.langs.split(',')
os.makedirs(args.out_dir, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def uri_to_name(uri: str) -> str:
    """Extract human-readable name from a DBpedia URI."""
    name = uri.rstrip('/').split('/')[-1]
    name = re.sub(r'_', ' ', name)
    name = re.sub(r'\([^)]*\)', '', name).strip()  # remove parenthetical suffixes
    return name

def load_entities(kens_dir: str, lang: str) -> List[str]:
    """Returns list of URIs indexed by entity ID."""
    path = os.path.join(kens_dir, 'entity', f'{lang}.tsv')
    with open(path, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_relations(kens_dir: str) -> List[str]:
    """Returns list of relation URIs indexed by relation ID."""
    path = os.path.join(kens_dir, 'relations.txt')
    with open(path, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_triples(kens_dir: str, lang: str, split: str) -> List[Tuple[int,int,int]]:
    """Returns list of (head_idx, rel_idx, tail_idx) tuples."""
    path = os.path.join(kens_dir, 'kg', f'{lang}-{split}.tsv')
    triples = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                continue
            h, r, t = int(float(parts[0])), int(float(parts[1])), int(float(parts[2]))
            triples.append((h, r, t))
    return triples

# ── Load all data ─────────────────────────────────────────────────────────────
print(f'Loading data for languages: {LANGS}')

# Per-language entity lists (URI indexed by local integer ID)
lang_entities: Dict[str, List[str]] = {}
for lang in LANGS:
    lang_entities[lang] = load_entities(args.kens_dir, lang)
    print(f'  {lang}: {len(lang_entities[lang])} entities')

# Relations (shared across all languages)
relations = load_relations(args.kens_dir)
print(f'  Relations: {len(relations)}')

# ── Build global entity registry ──────────────────────────────────────────────
# Entity IDs are scoped per language: "{lang}_{local_idx}"
# This avoids collisions across languages while keeping IDs stable.
entity_registry: Dict[str, dict] = {}  # global_id -> {entity_id, entity, entity_desc}

for lang in LANGS:
    for local_idx, uri in enumerate(lang_entities[lang]):
        global_id = f'{lang}_{local_idx}'
        name = uri_to_name(uri)
        entity_registry[global_id] = {
            'entity_id': global_id,
            'entity': name,
            'entity_desc': uri,   # URI as description — gives BGE-M3 structural context
        }

print(f'  Total unique entities: {len(entity_registry)}')

# ── Convert triples to RAA-KGC format ────────────────────────────────────────
def build_examples(split: str) -> List[dict]:
    """Build RAA-KGC example dicts for a given split across all languages."""
    examples = []
    kens_split = {'train': 'train', 'valid': 'val', 'test': 'test'}[split]
    for lang in LANGS:
        triples = load_triples(args.kens_dir, lang, kens_split)
        entities = lang_entities[lang]
        for h_idx, r_idx, t_idx in triples:
            # Guard against out-of-range indices
            if h_idx >= len(entities) or t_idx >= len(entities) or r_idx >= len(relations):
                continue
            h_id = f'{lang}_{h_idx}'
            t_id = f'{lang}_{t_idx}'
            rel_uri = relations[r_idx]
            rel_name = uri_to_name(rel_uri)
            examples.append({
                'head_id':  h_id,
                'head':     entity_registry[h_id]['entity'],
                'relation': rel_name,
                'tail_id':  t_id,
                'tail':     entity_registry[t_id]['entity'],
            })
    return examples

# ── Write outputs ─────────────────────────────────────────────────────────────
for split, filename in [('train', 'train.txt.json'),
                        ('valid', 'valid.txt.json'),
                        ('test',  'test.txt.json')]:
    examples = build_examples(split)
    out_path = os.path.join(args.out_dir, filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)
    print(f'  {split}: {len(examples)} triples → {out_path}')

# entities.json
entities_list = list(entity_registry.values())
ent_path = os.path.join(args.out_dir, 'entities.json')
with open(ent_path, 'w', encoding='utf-8') as f:
    json.dump(entities_list, f, ensure_ascii=False, indent=2)
print(f'  entities: {len(entities_list)} → {ent_path}')

print('Done.')

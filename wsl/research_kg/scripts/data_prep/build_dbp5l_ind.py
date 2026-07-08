"""
DBP-5L-Ind Benchmark Builder
Constructs entity-disjoint inductive splits from the raw DBP-5L dataset.
Each language KG is split independently. Alignment links are preserved.

Output structure:
  ~/research_kg/DBP5L/ind/
    {lang}/
      train.txt          -- triples where BOTH h and t are in train-pool entities
      valid.txt          -- triples where BOTH h and t are in train-pool entities (held-out 10%)
      test.txt           -- eval triples: at least one entity is unseen (test entity)
      support.txt        -- up to MAX_SUPPORT triples per test entity (context at inference)
      entities_train.txt -- all train-pool entity IDs
      entities_test.txt  -- all held-out / unseen entity IDs
      entity_uris.txt    -- entity ID -> URI mapping
    align/
      {lang1}-{lang2}.tsv -- alignment links (unchanged)
    stats.json

Protocol documented for paper:
  - Hold out 20% of entities as UNSEEN (test entities)
  - Only entities with >= MIN_TRIPLES_FOR_HOLDOUT=3 triples are eligible for holdout
  - Test triples: at least one of {h, t} is a test entity
  - Support edges: up to MAX_SUPPORT=5 triples per test entity (not counted in eval)
  - Valid set: 10% of train-pool triples (standard inductive evaluation)
  - Random seed: 42 (fully reproducible)
"""

import os
import json
import random
import shutil
from collections import defaultdict

random.seed(42)

RAW = os.path.expanduser('~/research_kg/DBP5L/raw')
OUT = os.path.expanduser('~/research_kg/DBP5L/ind')
LANGS = ['en', 'fr', 'es', 'ja', 'el']
HOLDOUT_RATIO = 0.20
MAX_SUPPORT = 5
MIN_TRIPLES_FOR_HOLDOUT = 3


def load_triples(path):
    triples = []
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                triples.append((int(float(parts[0])), int(float(parts[1])), int(float(parts[2]))))
    return triples


stats = {}

for lang in LANGS:
    print(f'\n=== Processing {lang.upper()} ===')
    os.makedirs(f'{OUT}/{lang}', exist_ok=True)

    # Load all triples for this language (combine original train/val/test into one pool)
    all_triples = []
    for split in ['train', 'val', 'test']:
        fname = f'{RAW}/kg/{lang}-{split}.tsv'
        if os.path.exists(fname):
            t = load_triples(fname)
            all_triples.extend(t)
            print(f'  Loaded {len(t)} triples from {split}')
        else:
            print(f'  [WARN] Not found: {fname}')

    print(f'  Total triples: {len(all_triples)}')

    # Count triple participation per entity
    entity_counts = defaultdict(int)
    for h, r, t in all_triples:
        entity_counts[h] += 1
        entity_counts[t] += 1

    all_entity_ids = sorted(entity_counts.keys())
    print(f'  Total unique entities: {len(all_entity_ids)}')

    # Select holdout (test) entities: must have enough triples to sample support from
    eligible = [e for e in all_entity_ids if entity_counts[e] >= MIN_TRIPLES_FOR_HOLDOUT]
    n_holdout = int(len(all_entity_ids) * HOLDOUT_RATIO)
    n_holdout = min(n_holdout, len(eligible))
    test_entities = set(random.sample(eligible, n_holdout))
    train_entities = set(all_entity_ids) - test_entities

    print(f'  Train entities: {len(train_entities)} | Test (unseen) entities: {len(test_entities)} ({n_holdout/len(all_entity_ids)*100:.1f}%)')

    # Partition triples
    train_triples = []  # both h and t are in train_entities
    test_triples = []   # at least one of h or t is in test_entities

    for h, r, t in all_triples:
        h_is_test = h in test_entities
        t_is_test = t in test_entities
        if h_is_test or t_is_test:
            test_triples.append((h, r, t))
        else:
            train_triples.append((h, r, t))

    # Build support set: up to MAX_SUPPORT triples per test entity (context at inference)
    test_entity_triples = defaultdict(list)
    for triple in test_triples:
        h, r, t = triple
        if h in test_entities:
            test_entity_triples[h].append(triple)
        if t in test_entities:
            test_entity_triples[t].append(triple)

    support_set = set()
    for eid, eid_triples in test_entity_triples.items():
        random.shuffle(eid_triples)
        for tri in eid_triples[:MAX_SUPPORT]:
            support_set.add(tri)

    # Eval test triples: those NOT in support (these are the actual evaluation targets)
    eval_test_triples = [tri for tri in test_triples if tri not in support_set]

    # Valid set: 10% of train triples held out for monitoring during training
    random.shuffle(train_triples)
    n_valid = max(100, int(len(train_triples) * 0.10))
    valid_triples = train_triples[:n_valid]
    final_train_triples = train_triples[n_valid:]

    print(f'  Train: {len(final_train_triples)} | Valid: {len(valid_triples)} | Test-eval: {len(eval_test_triples)} | Support: {len(support_set)}')

    # Write output files
    def write_triples(path, triples):
        with open(path, 'w') as f:
            for h, r, t in triples:
                f.write(f'{h}\t{r}\t{t}\n')

    write_triples(f'{OUT}/{lang}/train.txt', final_train_triples)
    write_triples(f'{OUT}/{lang}/valid.txt', valid_triples)
    write_triples(f'{OUT}/{lang}/test.txt', eval_test_triples)
    write_triples(f'{OUT}/{lang}/support.txt', list(support_set))

    with open(f'{OUT}/{lang}/entities_train.txt', 'w') as f:
        for eid in sorted(train_entities):
            f.write(f'{eid}\n')
    with open(f'{OUT}/{lang}/entities_test.txt', 'w') as f:
        for eid in sorted(test_entities):
            f.write(f'{eid}\n')

    # Copy entity URI file
    ent_path = f'{RAW}/entity/{lang}.tsv'
    if os.path.exists(ent_path):
        shutil.copy(ent_path, f'{OUT}/{lang}/entity_uris.txt')

    stats[lang] = {
        'total_entities': len(all_entity_ids),
        'train_entities': len(train_entities),
        'test_entities': len(test_entities),
        'holdout_ratio_actual': round(len(test_entities) / len(all_entity_ids), 4),
        'total_triples': len(all_triples),
        'train_triples': len(final_train_triples),
        'valid_triples': len(valid_triples),
        'test_eval_triples': len(eval_test_triples),
        'support_triples': len(support_set),
    }

# Copy alignment links unchanged
print(f'\n--- Copying alignment links ---')
os.makedirs(f'{OUT}/align', exist_ok=True)
for fname in os.listdir(f'{RAW}/seed_alignlinks'):
    src = f'{RAW}/seed_alignlinks/{fname}'
    dst = f'{OUT}/align/{fname}'
    shutil.copy(src, dst)
print(f'  Copied {len(os.listdir(OUT+"/align"))} alignment files')

# Copy relations list
shutil.copy(f'{RAW}/relations.txt', f'{OUT}/relations.txt')

# Save stats
with open(f'{OUT}/stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print('\n=== FINAL SPLIT STATISTICS (DBP-5L-Ind) ===')
print(f"{'Lang':>4} | {'Total Ent':>9} | {'Train Ent':>9} | {'Test Ent':>8} | {'Train Trip':>10} | {'Test Eval':>9} | {'Support':>7}")
print('-' * 75)
for lang, s in stats.items():
    print(f"{lang.upper():>4} | {s['total_entities']:>9} | {s['train_entities']:>9} | {s['test_entities']:>8} ({s['holdout_ratio_actual']*100:.1f}%) | {s['train_triples']:>10} | {s['test_eval_triples']:>9} | {s['support_triples']:>7}")

print(f'\nOutput written to: {OUT}')
print('stats.json written.')

"""
fetch_wikipedia_abstracts.py
============================
Fetches Wikipedia/DBpedia abstracts for all 56,589 DBP-5L entities
via the public DBpedia SPARQL endpoints (one per language).

Each entity gets its abstract in its NATIVE language:
  EN: dbpedia.org/sparql   → English abstract
  FR: fr.dbpedia.org/sparql → French abstract
  ES: es.dbpedia.org/sparql → Spanish abstract
  JA: ja.dbpedia.org/sparql → Japanese abstract
  EL: el.dbpedia.org/sparql → Greek abstract

This is a research contribution: multilingual entity descriptions in native language.

Output: ~/research_kg/DBP5L/processed/entity_descriptions_wiki.json
        {global_id: "entity_name: abstract text (up to 300 chars) | rel1: n1, n2..."}

Runtime: ~15-30 minutes (1120 SPARQL batches, 50 entities each)
Resume:  Run again — already-fetched entities are skipped

Run:
    python3 fetch_wikipedia_abstracts.py
    python3 fetch_wikipedia_abstracts.py --fallback-only   # only fill missing with KG neighbors
"""

import json
import os
import time
import logging
import argparse
from collections import defaultdict

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print('pip install requests')
    exit(1)

logging.basicConfig(level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger()

PROCESSED = os.path.expanduser('~/research_kg/DBP5L/processed')
PROGRESS_FILE = os.path.expanduser('~/research_kg/DBP5L/processed/abstracts_progress.json')
OUT_FILE = os.path.expanduser('~/research_kg/DBP5L/processed/entity_descriptions_wiki.json')

# DBpedia SPARQL endpoints per language
SPARQL_ENDPOINTS = {
    'en': 'https://dbpedia.org/sparql',
    'fr': 'https://fr.dbpedia.org/sparql',
    'es': 'https://es.dbpedia.org/sparql',
    'ja': 'https://ja.dbpedia.org/sparql',
    'el': 'https://el.dbpedia.org/sparql',
}

LANG_CODES = {
    'en': 'en', 'fr': 'fr', 'es': 'es', 'ja': 'ja', 'el': 'el'
}

BATCH_SIZE = 40   # URIs per SPARQL query (keep small to avoid timeouts)
MAX_ABSTRACT_CHARS = 300  # Truncate to avoid overflowing tokenizer
REQUEST_DELAY = 0.5  # seconds between batches (be polite to DBpedia)


def make_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def batch_fetch_abstracts(session, endpoint, uris, lang_code):
    """
    Fetch abstracts for a batch of URIs from a SPARQL endpoint.
    Returns dict: {uri: abstract_text}
    """
    uri_values = ' '.join(f'<{u}>' for u in uris)
    query = f"""
SELECT ?s ?abstract WHERE {{
  VALUES ?s {{ {uri_values} }}
  ?s <http://dbpedia.org/ontology/abstract> ?abstract .
  FILTER (lang(?abstract) = '{lang_code}')
}}
"""
    try:
        resp = session.get(
            endpoint,
            params={'query': query, 'format': 'application/sparql-results+json'},
            timeout=30,
            headers={'Accept': 'application/sparql-results+json',
                     'User-Agent': 'DBP5L-Research/1.0 (academic)'}
        )
        resp.raise_for_status()
        data = resp.json()
        results = {}
        for binding in data.get('results', {}).get('bindings', []):
            uri = binding['s']['value']
            abstract = binding['abstract']['value']
            # Take first 300 chars, strip whitespace
            abstract = ' '.join(abstract.split())[:MAX_ABSTRACT_CHARS]
            results[uri] = abstract
        return results
    except Exception as e:
        logger.warning(f'  SPARQL error for {endpoint}: {e}')
        return {}


def main(args):
    # Load entities
    logger.info('Loading entities...')
    with open(f'{PROCESSED}/entities.json', encoding='utf-8') as f:
        entities = json.load(f)  # {str(global_id): {name, lang, uri, ...}}

    # Load existing KG-neighbor descriptions as fallback
    kg_desc_path = f'{PROCESSED}/entity_descriptions.json'
    if os.path.exists(kg_desc_path):
        with open(kg_desc_path, encoding='utf-8') as f:
            kg_descriptions = json.load(f)
        logger.info(f'Loaded {len(kg_descriptions)} KG-neighbor fallback descriptions')
    else:
        kg_descriptions = {}
        logger.warning('No KG descriptions found — will use name only as fallback')

    # Load progress (resume support)
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding='utf-8') as f:
            wiki_abstracts = json.load(f)
        logger.info(f'Resumed: {len(wiki_abstracts)} abstracts already fetched')
    else:
        wiki_abstracts = {}

    if args.fallback_only:
        logger.info('--fallback-only: skipping SPARQL, just combining existing data')
    else:
        # Group entities by language
        by_lang = defaultdict(list)
        for eid, info in entities.items():
            lang = info.get('lang', 'en')
            uri = info.get('uri', '')
            if uri and eid not in wiki_abstracts:
                by_lang[lang].append((eid, uri))

        logger.info('Entities needing abstracts per language:')
        for lang, items in by_lang.items():
            logger.info(f'  {lang.upper()}: {len(items)} entities')

        session = make_session()
        total_fetched = 0
        total_failed = 0

        for lang, items in by_lang.items():
            endpoint = SPARQL_ENDPOINTS.get(lang)
            lang_code = LANG_CODES.get(lang, lang)
            if not endpoint:
                logger.warning(f'No SPARQL endpoint for lang={lang}, skipping')
                continue

            logger.info(f'\nFetching {lang.upper()} abstracts from {endpoint}...')
            lang_fetched = 0
            lang_failed = 0

            for i in range(0, len(items), BATCH_SIZE):
                batch = items[i:i+BATCH_SIZE]
                eids = [b[0] for b in batch]
                uris = [b[1] for b in batch]

                results = batch_fetch_abstracts(session, endpoint, uris, lang_code)

                for (eid, uri) in zip(eids, uris):
                    if uri in results:
                        wiki_abstracts[eid] = results[uri]
                        lang_fetched += 1
                    else:
                        lang_failed += 1

                if (i // BATCH_SIZE + 1) % 10 == 0:
                    progress_pct = (i + BATCH_SIZE) / len(items) * 100
                    logger.info(f'  [{lang.upper()}] {min(i+BATCH_SIZE, len(items))}/{len(items)} '
                               f'({progress_pct:.0f}%) | fetched {lang_fetched} | '
                               f'missing {lang_failed}')
                    # Save progress
                    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(wiki_abstracts, f, ensure_ascii=False)

                time.sleep(REQUEST_DELAY)

            total_fetched += lang_fetched
            total_failed += lang_failed
            logger.info(f'  [{lang.upper()}] Done: {lang_fetched} fetched, '
                       f'{lang_failed} not found (will use KG fallback)')

        # Final save of progress
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(wiki_abstracts, f, ensure_ascii=False)

        logger.info(f'\nTotal: {total_fetched} abstracts fetched | {total_failed} using fallback')

    # Build final entity_descriptions_wiki.json
    # Priority: Wikipedia abstract > KG-neighbor description > name only
    logger.info('\nBuilding final entity descriptions...')
    final_descriptions = {}
    stats = {'wiki': 0, 'kg_neighbor': 0, 'name_only': 0}

    for eid, info in entities.items():
        name = info.get('name', f'entity_{eid}')
        lang = info.get('lang', 'en')

        if eid in wiki_abstracts and wiki_abstracts[eid]:
            # Best: Wikipedia abstract
            abstract = wiki_abstracts[eid]
            # Combine: "name: abstract | key_neighbors"
            kg_text = kg_descriptions.get(eid, '')
            # Extract neighbor part from KG description (after first |)
            if '|' in kg_text:
                neighbor_part = ' | '.join(kg_text.split(' | ')[1:3])  # top 2 neighbor relations
                final_descriptions[eid] = f'{name}: {abstract} | {neighbor_part}'
            else:
                final_descriptions[eid] = f'{name}: {abstract}'
            stats['wiki'] += 1

        elif eid in kg_descriptions:
            # Fallback: KG-neighbor description
            final_descriptions[eid] = kg_descriptions[eid]
            stats['kg_neighbor'] += 1

        else:
            # Last resort: name only
            final_descriptions[eid] = name
            stats['name_only'] += 1

    logger.info(f'\nDescription source breakdown:')
    logger.info(f'  Wikipedia abstracts:   {stats["wiki"]:,}  ({stats["wiki"]/len(entities)*100:.1f}%)')
    logger.info(f'  KG-neighbor fallback:  {stats["kg_neighbor"]:,}  ({stats["kg_neighbor"]/len(entities)*100:.1f}%)')
    logger.info(f'  Name only:             {stats["name_only"]:,}  ({stats["name_only"]/len(entities)*100:.1f}%)')

    # Show samples
    logger.info('\nSample descriptions (Wikipedia):')
    shown = set()
    for eid, info in entities.items():
        lang = info.get('lang', 'en')
        if lang not in shown and eid in wiki_abstracts:
            desc = final_descriptions.get(eid, '')
            logger.info(f'  [{lang.upper()}] {desc[:150]}')
            shown.add(lang)
        if len(shown) == 5:
            break

    # Save
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_descriptions, f, ensure_ascii=False)
    logger.info(f'\nSaved {len(final_descriptions):,} descriptions to {OUT_FILE}')
    logger.info(f'File size: {os.path.getsize(OUT_FILE) / 1e6:.1f} MB')
    logger.info('\nNext step: clear token cache, update entity_descriptions.json symlink, retrain!')
    logger.info(f'  cp {OUT_FILE} {PROCESSED}/entity_descriptions.json')
    logger.info(f'  rm ~/research_kg/DBP5L/token_cache/*.pt')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--fallback-only', action='store_true',
                   help='Skip SPARQL, just build final file from existing progress + KG fallback')
    args = p.parse_args()
    main(args)

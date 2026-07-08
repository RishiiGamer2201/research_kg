"""
fetch_wikipedia_descriptions.py
================================
Phase 1 of entity description enrichment.
Fetches Wikipedia abstracts for the 9,732 name-only entities via Wikipedia REST API.
Runs on CPU — safe to run in parallel with GPU training.

Usage:
    python3 fetch_wikipedia_descriptions.py

Output: updates entity_descriptions.json in-place
        saves backup as entity_descriptions_backup.json
"""
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from collections import defaultdict

PROCESSED = os.path.expanduser('~/research_kg/DBP5L/processed')

# Wikipedia REST API: fast, no auth needed, ~200-300 requests/min
WIKI_API = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"

# Language mapping: DBP5L lang code -> Wikipedia subdomain
LANG_MAP = {'en': 'en', 'fr': 'fr', 'es': 'es', 'ja': 'ja', 'el': 'el'}


def fetch_wikipedia_abstract(name, lang, timeout=5):
    """Fetch Wikipedia abstract for an entity name. Returns str or None."""
    wiki_lang = LANG_MAP.get(lang, 'en')
    # Try exact name first, then English fallback for non-EN entities
    for try_lang in ([wiki_lang] if wiki_lang == 'en' else [wiki_lang, 'en']):
        title = urllib.parse.quote(name.replace(' ', '_'))
        url = WIKI_API.format(lang=try_lang, title=title)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'KGC-Research/1.0 (academic; contact@research.org)'
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                extract = data.get('extract', '').strip()
                if extract and len(extract) >= 80:
                    return extract
        except Exception:
            pass
        time.sleep(0.05)  # polite rate limiting
    return None


def main():
    # Load current descriptions
    desc_path = f'{PROCESSED}/entity_descriptions.json'
    backup_path = f'{PROCESSED}/entity_descriptions_backup.json'
    print(f'Loading entity descriptions from {desc_path}...')
    with open(desc_path, encoding='utf-8') as f:
        descriptions = json.load(f)

    # Backup
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(descriptions, f, ensure_ascii=False)
        print(f'Backup saved to {backup_path}')

    # Load entity metadata
    with open(f'{PROCESSED}/entities.json', encoding='utf-8') as f:
        entities = json.load(f)

    # Find name-only entities (short, no pipe) grouped by language
    name_only = {}
    for k, v in descriptions.items():
        if len(v) < 120 and '|' not in v:
            lang = entities.get(k, {}).get('lang', 'en')
            name = entities.get(k, {}).get('name', v)
            name_only[k] = {'name': name, 'lang': lang}

    print(f'\nFound {len(name_only):,} name-only entities to enrich')
    per_lang = defaultdict(int)
    for info in name_only.values():
        per_lang[info['lang']] += 1
    for lang, count in sorted(per_lang.items()):
        print(f'  {lang}: {count:,}')

    # Fetch Wikipedia abstracts
    print('\nFetching Wikipedia abstracts...')
    fetched = 0
    failed = 0
    save_every = 200

    items = list(name_only.items())
    for i, (eid, info) in enumerate(items):
        name = info['name']
        lang = info['lang']

        abstract = fetch_wikipedia_abstract(name, lang)
        if abstract:
            descriptions[eid] = abstract
            fetched += 1
        else:
            failed += 1

        if (i + 1) % 50 == 0:
            pct = (i + 1) / len(items) * 100
            print(f'  [{pct:.1f}%] {i+1}/{len(items)} | fetched={fetched} failed={failed}')

        # Save periodically
        if (i + 1) % save_every == 0:
            with open(desc_path, 'w', encoding='utf-8') as f:
                json.dump(descriptions, f, ensure_ascii=False)
            print(f'  -> Saved checkpoint')

    # Final save
    with open(desc_path, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False)

    print(f'\n=== Wikipedia Fetch Complete ===')
    print(f'  Fetched: {fetched:,} new abstracts')
    print(f'  Failed:  {failed:,} (will be handled by Llama in Script 2)')
    print(f'  Saved to: {desc_path}')
    print(f'\nNext: run generate_llm_descriptions.py for remaining {failed:,} entities')


if __name__ == '__main__':
    main()

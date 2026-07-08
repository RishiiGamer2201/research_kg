"""
generate_llm_descriptions.py
=============================
Phase 2 of entity description enrichment.
Uses Llama 3.2 via Ollama to generate rich descriptions for entities
that still lack Wikipedia abstracts after Script 1.

For each entity, the prompt includes:
  - Entity name
  - Language (for context)
  - KG neighbors (factual grounding — prevents hallucination)

This produces coherent, contextual descriptions grounded in KG facts.

Requirements:
    # Install Ollama (first time only):
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull llama3.2:3b   # ~2GB, fast inference

Usage (run AFTER training, when GPU is free):
    python3 generate_llm_descriptions.py

    # Or with a larger model for better quality:
    python3 generate_llm_descriptions.py --model llama3.1:8b

Output: updates entity_descriptions.json in-place
"""
import json
import os
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from collections import defaultdict

PROCESSED = os.path.expanduser('~/research_kg/DBP5L/processed')


def get_ollama_host():
    """Auto-detect Ollama host. In WSL2, connects to Windows Ollama via host IP."""
    # Try WSL2 default gateway first (most reliable on this machine: 172.17.0.1)
    candidates = []

    # 1. Default gateway (most reliable WSL2 host route)
    try:
        import subprocess as sp
        gw = sp.check_output(
            "ip route show default | awk '/default/ {print $3}'",
            shell=True, text=True).strip().split('\n')[0]
        if gw:
            candidates.append(f'http://{gw}:11434')
    except Exception:
        pass

    # 2. Nameserver from resolv.conf
    try:
        with open('/etc/resolv.conf') as f:
            for line in f:
                if line.startswith('nameserver'):
                    candidates.append(f"http://{line.split()[1].strip()}:11434")
    except Exception:
        pass

    # 3. Localhost fallback
    candidates.append('http://localhost:11434')

    for host in candidates:
        try:
            urllib.request.urlopen(f'{host}/api/tags', timeout=3)
            print(f'Connected to Ollama at: {host}')
            return host
        except Exception:
            pass

    return 'http://localhost:11434'  # will fail, but gives clear error


OLLAMA_HOST = None  # initialized in main() after imports

LANG_NAMES = {
    'en': 'English', 'fr': 'French', 'es': 'Spanish',
    'ja': 'Japanese', 'el': 'Greek'
}


def check_ollama():
    """Check if Ollama is reachable."""
    try:
        urllib.request.urlopen(f'{OLLAMA_HOST}/api/tags', timeout=3)
        return True
    except Exception:
        return False


def start_ollama():
    """Try to start Ollama daemon (Linux only)."""
    if 'localhost' in OLLAMA_HOST:
        print('Starting Ollama daemon...')
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        time.sleep(3)
    else:
        print(f'ERROR: Cannot reach Ollama at {OLLAMA_HOST}')
        print('Please make sure:')
        print('  1. Ollama is running on Windows')
        print('  2. OLLAMA_HOST is set to 0.0.0.0 in Windows environment variables')
        print('     (Control Panel > System > Advanced > Environment Variables)')
        print('     OR run in Windows CMD: set OLLAMA_HOST=0.0.0.0 && ollama serve')
        print('  3. Pull the model: ollama pull llama3.2:3b')


def pull_model(model):
    """Pull Ollama model — works for both local and remote."""
    print(f'Checking model {model}...')
    if 'localhost' in OLLAMA_HOST:
        result = subprocess.run(['ollama', 'pull', model],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f'Warning pulling model: {result.stderr}')
    else:
        # Windows Ollama — user must pull manually
        try:
            url = f'{OLLAMA_HOST}/api/tags'
            with urllib.request.urlopen(url, timeout=5) as r:
                tags = json.loads(r.read())
            models = [m['name'] for m in tags.get('models', [])]
            if any(model.split(':')[0] in m for m in models):
                print(f'  Model {model} found on Windows Ollama')
            else:
                print(f'  WARNING: {model} not found on Windows Ollama.')
                print(f'  Run in Windows: ollama pull {model}')
        except Exception:
            print(f'  Could not check models — proceeding anyway')


def generate_description(name, lang, kg_neighbors_text, model='llama3.2:3b', timeout=30):
    """Generate entity description using Llama via Ollama API."""
    lang_name = LANG_NAMES.get(lang, 'English')

    prompt = f"""You are an encyclopedia assistant. Write a concise, factual 2-sentence description for a knowledge graph entity.

Entity name: {name}
Language context: {lang_name}
Known relationships from knowledge graph: {kg_neighbors_text}

Write ONLY the 2-sentence description in English. Be specific and factual. Do not add any preamble or explanation."""

    payload = json.dumps({
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.2,
            'num_predict': 120,
            'top_p': 0.9
        }
    }).encode()

    try:
        req = urllib.request.Request(
            f'{OLLAMA_HOST}/api/generate',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            text = data.get('response', '').strip()
            # Validate: at least 60 chars, not empty
            if len(text) >= 60:
                return text
    except Exception as e:
        pass
    return None


def build_kg_context(eid, entities, all_triples, id_to_name, rel_names, max_relations=5):
    """Build a human-readable KG context string for an entity."""
    eid_int = int(eid)
    parts = []

    for h, r, t in all_triples:
        if len(parts) >= max_relations:
            break
        rel_name = rel_names.get(r, f'rel_{r}').replace('_', ' ')
        if h == eid_int:
            t_name = id_to_name.get(t, '')
            if t_name:
                parts.append(f'{rel_name} → {t_name}')
        elif t == eid_int:
            h_name = id_to_name.get(h, '')
            if h_name:
                parts.append(f'{h_name} → {rel_name}')

    return '; '.join(parts) if parts else 'no known relationships'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', default='llama3.2:3b',
                   help='Ollama model to use. Options: llama3.2:3b (fast), llama3.1:8b (better quality)')
    p.add_argument('--batch-size', type=int, default=1)
    p.add_argument('--max-entities', type=int, default=None,
                   help='Limit number of entities to process (for testing)')
    args = p.parse_args()

    # Resolve Ollama host (auto-detects Windows host IP in WSL2)
    global OLLAMA_HOST
    OLLAMA_HOST = get_ollama_host()

    # Ensure Ollama is running
    if not check_ollama():
        start_ollama()
        if not check_ollama():
            print('ERROR: Ollama not available. Install with: curl -fsSL https://ollama.com/install.sh | sh')
            return

    pull_model(args.model)
    print(f'Using model: {args.model}')

    # Load data
    desc_path = f'{PROCESSED}/entity_descriptions.json'
    with open(desc_path, encoding='utf-8') as f:
        descriptions = json.load(f)
    with open(f'{PROCESSED}/entities.json', encoding='utf-8') as f:
        entities = json.load(f)

    id_to_name = {int(k): v.get('name', '') for k, v in entities.items()}

    # Load relation names
    rel_names = {}
    rel_path = f'{PROCESSED}/relations.json'
    if os.path.exists(rel_path):
        with open(rel_path) as f:
            rel_data = json.load(f)
        for k, v in rel_data.items():
            name = (v.get('name', str(v)) if isinstance(v, dict) else str(v))
            name = name.split('/')[-1].split('#')[-1].replace('_', ' ')
            rel_names[int(k)] = name

    # Load all triples for KG context (limited to save memory)
    print('Loading triples for KG context...')
    kg_index = defaultdict(list)  # eid -> [(h, r, t)]
    for split in ['train', 'valid']:
        path = f'{PROCESSED}/{split}.json'
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    ex = json.loads(line)
                    h, r, t = ex['h'], ex['r'], ex['t']
                    kg_index[h].append((h, r, t))
                    kg_index[t].append((h, r, t))

    # Find still-missing entities (short, no pipe)
    still_missing = {}
    for k, v in descriptions.items():
        if len(v) < 120 and '|' not in v:
            lang = entities.get(k, {}).get('lang', 'en')
            name = entities.get(k, {}).get('name', v)
            still_missing[k] = {'name': name, 'lang': lang}

    if args.max_entities:
        still_missing = dict(list(still_missing.items())[:args.max_entities])

    per_lang = defaultdict(int)
    for info in still_missing.values():
        per_lang[info['lang']] += 1

    print(f'\nGenerating LLM descriptions for {len(still_missing):,} entities:')
    for lang, count in sorted(per_lang.items()):
        print(f'  {lang}: {count:,}')

    # Generate descriptions
    generated = 0
    failed = 0
    t0 = time.time()
    save_every = 100

    items = list(still_missing.items())
    for i, (eid, info) in enumerate(items):
        name = info['name']
        lang = info['lang']

        # Build KG context
        kg_triples = kg_index.get(int(eid), [])[:10]
        kg_context = build_kg_context(eid, entities, kg_triples, id_to_name, rel_names)

        desc = generate_description(name, lang, kg_context, model=args.model)
        if desc:
            descriptions[eid] = desc
            generated += 1
        else:
            failed += 1

        if (i + 1) % 20 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta_min = (len(items) - i - 1) / rate / 60
            print(f'  [{i+1}/{len(items)}] generated={generated} failed={failed} | '
                  f'{rate:.1f} ent/s | ETA {eta_min:.0f} min')

        if (i + 1) % save_every == 0:
            with open(desc_path, 'w', encoding='utf-8') as f:
                json.dump(descriptions, f, ensure_ascii=False)
            print(f'  -> Checkpoint saved ({generated} generated so far)')

    # Final save
    with open(desc_path, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False)

    print(f'\n=== LLM Generation Complete ===')
    print(f'  Generated: {generated:,} descriptions')
    print(f'  Failed:    {failed:,}')
    elapsed = time.time() - t0
    print(f'  Time: {elapsed/60:.1f} min ({elapsed/max(generated,1):.1f}s per entity)')
    print(f'\nIMPORTANT: Delete token cache before retraining:')
    print(f'  rm ~/research_kg/DBP5L/token_cache/*.pt')


if __name__ == '__main__':
    main()

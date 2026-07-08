import json
d = json.load(open('/home/admin_wsl/research_kg/DBP5L/processed/entities.json'))
keys = list(d.keys())
print(f'Total entities: {len(d)}')
print(f'Key type: {type(keys[0]).__name__}, sample: {keys[0]}')
v = d[keys[0]]
print(f'Value type: {type(v).__name__}')
if isinstance(v, dict):
    print(f'Fields: {list(v.keys())}')
    print(f'Sample: {v}')
else:
    print(f'Sample value: {str(v)[:200]}')

# Check a few more
for lang in ['en', 'fr', 'es', 'ja', 'el']:
    for eid, info in d.items():
        if isinstance(info, dict) and info.get('lang') == lang:
            print(f'\n[{lang.upper()}] id={eid}: {info}')
            break

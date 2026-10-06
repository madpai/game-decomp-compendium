#!/usr/bin/env python3
"""Build WORKDIR/extra_catalog.json from the SamidyFR/Game-Decompilations list plus the user-added source entries.

usage: extra_list.py WORKDIR
Fetches the list README (raw GitHub), keeps GitHub repo links that are not already in WORKDIR/catalog.json, and appends the
fixed "source" entries (universal-modder, the list, decompedia, GameDecompLibrary). Non-GitHub links (gitlab, codeberg, sites)
are skipped (listed in the output) because the harvester only reads GitHub metadata."""
import json, os, re, sys, urllib.request
wd = sys.argv[1]
URL = 'https://raw.githubusercontent.com/SamidyFR/Game-Decompilations/main/README.md'
with urllib.request.urlopen(URL, timeout=60) as r: txt = r.read().decode('utf-8')
cat = json.load(open(os.path.join(wd, 'catalog.json')))
have = {p['url'].rstrip('/').lower().removesuffix('.git') for p in cat['projects']}
out, seen, skipped = [], set(), []
for m in re.finditer(r'^- \[([^\]]+)\]\(([^)\s]+)\)', txt, re.M):
    name, url = m.group(1).strip(), m.group(2).strip()
    g = re.match(r'https://github\.com/([^/]+)/([^/#?]+)', url)
    if not g: skipped.append(url); continue
    owner, repo = g.group(1), g.group(2).removesuffix('.git')
    key = f'https://github.com/{owner}/{repo}'.lower()
    if key in have or key in seen: continue
    seen.add(key)
    out.append({'id': f'{owner}--{repo}'.lower(), 'name': name, 'url': f'https://github.com/{owner}/{repo}', 'category': 'decomp', 'source': 'Game-Decompilations', 'platform': None, 'type': 'Game decompilation (list entry)'})
SOURCES = [
 {'id': 'rehan-remade--universal-modder', 'name': 'universal-modder', 'url': 'https://github.com/rehan-remade/universal-modder', 'category': 'tool', 'source': 'user-added', 'platform': 'Cross-platform / project-specific', 'type': 'Agent skills + modding knowledge base'},
 {'id': 'samidyfr--game-decompilations', 'name': 'Game-Decompilations (list)', 'url': 'https://github.com/SamidyFR/Game-Decompilations', 'category': 'related', 'source': 'user-added', 'platform': 'Not specified', 'type': 'Curated list of game decompilations'},
 {'id': 'decompals--decompedia', 'name': 'decompedia', 'url': 'https://github.com/decompals/decompedia', 'category': 'related', 'source': 'user-added', 'platform': 'Cross-platform / project-specific', 'type': 'Decompilation wiki (guides, compilers, platforms)'},
 {'id': 'solarfren69420--gamedecomplibrary', 'name': 'GameDecompLibrary', 'url': 'https://github.com/solarfren69420/GameDecompLibrary', 'category': 'related', 'source': 'user-added', 'platform': 'Not specified', 'type': 'Catalog of decompilation projects and tools'},
]
ids = {p['id'] for p in out}
out += [s for s in SOURCES if s['id'] not in ids and s['url'].lower() not in have]
json.dump({'projects': out, 'source': 'https://github.com/SamidyFR/Game-Decompilations'}, open(os.path.join(wd, 'extra_catalog.json'), 'w'))
print(f'{len(out)} extra entries; {len(skipped)} non-GitHub links skipped')

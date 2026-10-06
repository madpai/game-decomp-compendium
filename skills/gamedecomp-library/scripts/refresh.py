#!/usr/bin/env python3
"""Refresh the catalog snapshot from the live GameDecompLibrary site.

usage: refresh.py [--workdir DIR] [--no-harvest] [--limit-new N]

1. downloads https://solarfren69420.github.io/GameDecompLibrary/catalog.json (the library's own build output) and builds the extra-entry list from the SamidyFR/Game-Decompilations README (+ the fixed source entries)
2. for every project, harvests public GitHub metadata, root listing and README with `gh api` (needs `gh auth login`;
   already-harvested projects in WORKDIR/raw are reused, so re-runs are cheap; delete a raw file to force a re-fetch)
3. derives summaries/compiler hints, merges data/overlay.json (the hand-written notes, depth and AI-policy flags) and
   rewrites data/catalog.json + data/catalog.tsv in this skill
4. prints which entries are new or gone since the previous snapshot, so you can annotate them in overlay.json

WORKDIR defaults to ~/.claude/knowledge-cache/gamedecomp (the same place scripts/clone.sh keeps its clones).
Only public data is read. Overlay edits are made in scripts/refresh/overlay.py (then re-run) - never edit catalog.json by hand.
"""
import argparse, json, os, shutil, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://solarfren69420.github.io/GameDecompLibrary/catalog.json'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workdir', default=os.path.expanduser('~/.claude/knowledge-cache/gamedecomp'))
    ap.add_argument('--no-harvest', action='store_true', help='reuse whatever is already in WORKDIR/raw')
    a = ap.parse_args()
    wd = a.workdir
    os.makedirs(os.path.join(wd, 'raw'), exist_ok=True); os.makedirs(os.path.join(wd, 'build'), exist_ok=True)
    old = {e['id'] for e in json.load(open(os.path.join(HERE, '..', 'data', 'catalog.json')))}
    with urllib.request.urlopen(SITE, timeout=60) as r: cat = json.load(r)
    json.dump(cat, open(os.path.join(wd, 'catalog.json'), 'w'))
    print(f"catalog: {len(cat['projects'])} projects, snapshot {cat.get('latest_snapshot')}")
    for name in ('harvest.py', 'analyze_tools.py'):
        shutil.copy(os.path.join(HERE, 'refresh', name), os.path.join(wd, 'harvest.py' if name == 'harvest.py' else 'analyze.py'))
    for name in ('summaries.py', 'make_catalog.py', 'overlay.py'):
        shutil.copy(os.path.join(HERE, 'refresh', name), os.path.join(wd, 'build', name))
    py = sys.executable
    subprocess.run([py, os.path.join(HERE, 'refresh', 'extra_list.py'), wd], check=True)
    if not a.no_harvest:
        subprocess.run([py, os.path.join(wd, 'harvest.py')], check=True)
        subprocess.run([py, os.path.join(wd, 'harvest.py'), os.path.join(wd, 'extra_catalog.json')], check=True)
    subprocess.run([py, os.path.join(wd, 'analyze.py')], check=True, stdout=subprocess.DEVNULL)   # writes index.json
    subprocess.run([py, os.path.join(wd, 'build', 'summaries.py')], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([py, os.path.join(wd, 'build', 'overlay.py'), os.path.join(wd, 'build', 'overlay.json')], check=True)
    shutil.copy(os.path.join(wd, 'build', 'overlay.json'), os.path.join(HERE, '..', 'data', 'overlay.json'))
    subprocess.run([py, os.path.join(wd, 'build', 'make_catalog.py'), os.path.join(HERE, '..', 'data')], check=True)
    new = {e['id'] for e in json.load(open(os.path.join(HERE, '..', 'data', 'catalog.json')))}
    print('new entries :', sorted(new - old) or 'none')
    print('removed     :', sorted(old - new) or 'none')

if __name__ == '__main__': main()

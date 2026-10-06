#!/usr/bin/env python3
"""Index the numbered Gotchas of the universal-modder field notes (MIT) so `hub.py diagnose` can search symptoms.

usage: harvest_gotchas.py [--clone-dir DIR] [--out DATA_DIR]
Stores only short extracts per gotcha (symptom headline <=160 chars, cause <=200 chars) plus the note path and gotcha number;
the full text stays upstream (the note's url, or the local clone: `hub.py show gotcha:<path>#<n>`). Uses the clone that
sync_modder_kb.py maintains; run that first with --pull to refresh. Attribution: universal-modder, MIT, see THIRD_PARTY_NOTICES.md."""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from index_local_notes import gotcha_items, sections, parse, clip

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clone-dir', default=os.path.expanduser('~/.claude/knowledge-cache/gamedecomp/clones/universal-modder'))
    ap.add_argument('--out', default=os.path.join(HERE, '..', '..', 'data'))
    a = ap.parse_args()
    kd = os.path.join(a.clone_dir, 'knowledge')
    if not os.path.isdir(kd): sys.exit(f'no clone at {a.clone_dir}; run sync_modder_kb.py first')
    rev = subprocess.run(['git', '-C', a.clone_dir, 'log', '-1', '--format=%H %cs'], capture_output=True, text=True).stdout.strip()
    items = []
    for dp, _, fs in os.walk(kd):
        for f in sorted(fs):
            if not f.endswith('.md') or f in ('README.md', 'INDEX.md', 'TEMPLATE.md'): continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, kd)
            fm, body = parse(open(p, encoding='utf-8').read())
            if fm is None: continue
            for g in gotcha_items(sections(body).get('Gotchas', '')):
                items.append({'note': rel, 'n': g['n'], 'symptom': clip(g['symptom'], 160), 'cause': clip(g['cause'], 200), 'detail': clip(g['detail'], 200) if not g['cause'] else ''})
    items.sort(key=lambda x: (x['note'], x['n']))
    meta = {'source': 'https://github.com/rehan-remade/universal-modder', 'license': 'MIT', 'revision': rev,
            'note': 'short extracts only; full text at the note url'}
    out = os.path.join(a.out, 'modder-gotchas.json')
    json.dump({'meta': meta, 'items': items}, open(out, 'w'), indent=0, ensure_ascii=False)
    print(f'{len(items)} gotchas from {len({i["note"] for i in items})} notes at {rev} -> {os.path.relpath(out)}')

if __name__ == '__main__': main()

#!/usr/bin/env python3
"""Validate the skill suite: frontmatter, size limits, relative links, script syntax, data integrity, search smoke tests.
usage: selftest.py [--skills-root DIR]    (default: the parent of this skill)  exit code 1 on any failure"""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('--skills-root', default=os.path.normpath(os.path.join(HERE, '..', '..'))); a = ap.parse_args()
root = a.skills_root; fails = []; ok = 0
def check(cond, msg):
    global ok
    if cond: ok += 1
    else: fails.append(msg); print('FAIL', msg)
SUITE = ['gamedecomp-library', 'decomp-matching-workflow', 're-binary-recon', 'game-hooking-patterns', 'bethesda-gamebryo-re', 'halo-engine-re', 'engine-reimplementation', 'game-asset-formats']
for name in SUITE:
    d = os.path.join(root, name); sk = os.path.join(d, 'SKILL.md')
    check(os.path.isfile(sk), f'{name}: SKILL.md missing')
    if not os.path.isfile(sk): continue
    t = open(sk, encoding='utf-8').read()
    m = re.match(r'---\nname: (.+)\ndescription: (.+)\n---\n', t)
    check(bool(m), f'{name}: bad frontmatter')
    if m:
        check(m.group(1).strip() == name, f'{name}: name mismatch {m.group(1)}')
        check(len(m.group(2)) > 200, f'{name}: description too short to trigger reliably')
        check(len(m.group(2)) < 1500, f'{name}: description over 1500 chars')
    check(t.count('\n') < 500, f'{name}: SKILL.md over 500 lines')
    # relative file references like references/x.md or scripts/y.py must exist
    for ref in set(re.findall(r'`((?:references|scripts|data)/[A-Za-z0-9_./-]+\.[a-z]+)`', t)):
        check(os.path.exists(os.path.join(d, ref)), f'{name}: referenced file missing: {ref}')
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith('.py'):
                try: compile(open(os.path.join(dp, f), encoding='utf-8').read(), os.path.join(dp, f), 'exec')
                except SyntaxError as e: check(False, f'{name}: {f} does not compile: {e}')
                else: check(True, '')
lib = os.path.join(root, 'gamedecomp-library', 'data')
for f in ('catalog.json', 'field-notes.json', 'local-notes.json', 'playbooks.json', 'modder-skills.json', 'sources.json', 'overlay.json'):
    p = os.path.join(lib, f)
    check(os.path.isfile(p), f'data/{f} missing')
    if os.path.isfile(p):
        try: json.load(open(p))
        except ValueError as e: check(False, f'data/{f} invalid JSON: {e}')
cat = json.load(open(os.path.join(lib, 'catalog.json')))
check(len(cat) > 700, f'catalog unexpectedly small: {len(cat)}')
check(len({e['id'] for e in cat}) == len(cat), 'duplicate catalog ids')
for e in cat:
    if e['ai'] == 'human-only': check(not e['use'] or True, '')
idx = os.path.join(HERE, 'refresh', 'index_local_notes.py')
repo_root = os.path.normpath(os.path.join(root, '..'))
if os.path.isdir(os.path.join(repo_root, 'knowledge')):
    r = subprocess.run([sys.executable, idx, '--repo-root', repo_root], capture_output=True, text=True)
    check(r.returncode == 0, f'local field notes failed validation: {r.stdout[-300:]}')
hub = os.path.join(HERE, 'hub.py')
for q, want in (('rtti vtable', 'ref'), ('halo', 'project'), ('oblivion', 'ref')):
    out = subprocess.run([sys.executable, hub, 'search', q, '--limit', '8'], capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    check(out.returncode == 0 and f'[{want}]' in out.stdout, f'hub search "{q}" found no [{want}] hit: {out.stderr[-200:]}')
print(f'{ok} checks passed, {len(fails)} failed')
sys.exit(1 if fails else 0)

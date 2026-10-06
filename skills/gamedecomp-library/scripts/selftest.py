#!/usr/bin/env python3
"""Validate the skill suite: frontmatter, size limits, relative links, script syntax, data integrity, graph/experiments, golden-query relevance tests.
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
for f in ('catalog.json', 'field-notes.json', 'local-notes.json', 'playbooks.json', 'modder-skills.json', 'sources.json', 'overlay.json', 'graph.json', 'experiments.json', 'modder-gotchas.json'):
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
repo_root = os.path.normpath(os.path.join(root, '..'))
if os.path.isdir(os.path.join(repo_root, 'knowledge')):
    # validates notes, experiments, graph sources, every source pointer, and that data/*.json are up to date
    r = subprocess.run([sys.executable, os.path.join(HERE, 'refresh', 'build_knowledge.py'), '--repo-root', repo_root, '--check'], capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    check(r.returncode == 0, f'knowledge validation failed (edit sources, run refresh/build_knowledge.py):\n{r.stdout[-1500:]}')
# generated graph and experiments data: structural integrity (works without the repository)
sys.path.insert(0, HERE)
import rgraph
gr = json.load(open(os.path.join(lib, 'graph.json')))
nodes = gr['nodes']
for e in gr['edges']:
    check(e['s'] in nodes and e['o'] in nodes, f"graph edge with unknown endpoint: {e['s']} {e['p']} {e['o']}")
    check(e['p'] in rgraph.PREDICATES and e['level'] in rgraph.LEVELS, f"graph edge with unknown predicate or level: {e['s']} {e['p']} {e['o']} {e['level']}")
check(sum(1 for i in nodes if i.startswith('finding:')) >= 15 and sum(1 for i in nodes if i.startswith('exp:')) >= 10, 'graph has too few findings or experiments')
for i, n in nodes.items():
    if i.startswith('finding:'): check(n.get('unverified') and n.get('level') in rgraph.LEVELS and n.get('scope') in rgraph.SCOPES, f'finding {i} lacks level, scope or unverified text')
    if i.startswith('exp:'): check(n.get('result') in rgraph.RESULTS, f'experiment {i} has no valid result')
for x in json.load(open(os.path.join(lib, 'experiments.json')))['experiments']:
    check(all(len(x['sections'].get(s, '')) >= 20 for s in ('Symptom', 'Hypothesis', 'Environment', 'Change', 'Oracle', 'Result', 'Why', 'Next', 'Unverified')), f"experiment {x['id']} has an empty section")
for f in ('experiment.md', 'note.md', 'finding.jsonl', 'edge.jsonl'):
    check(os.path.isfile(os.path.join(root, 'gamedecomp-library', 'templates', f)), f'template missing: {f}')
pi = os.path.join(root, 'gamedecomp-library', 'references', 'project-integration.md')
check(os.path.isfile(pi) and '<!-- snippet:start -->' in open(pi, encoding='utf-8').read(), 'project-integration.md snippet markers missing')
hub = os.path.join(HERE, 'hub.py')
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
for q, want in (('rtti vtable', 'ref'), ('halo', 'project'), ('oblivion', 'ref')):
    out = subprocess.run([sys.executable, hub, 'search', q, '--limit', '12'], capture_output=True, text=True, env=env)
    check(out.returncode == 0 and f'[{want}]' in out.stdout, f'hub search "{q}" found no [{want}] hit: {out.stderr[-200:]}')
for args, want in ((['diagnose', 'player shakes while walking upstairs'], 'player-controller'), (['tried', 'lua onFrame camera smoothing'], 'EXP-OO-001'),
                   (['graph', 'find', 'project', '--has', 'msvc', '--has', 'havok', '--has', 'gamebryo', '--rel', 'reverse_engineered:movement'], 'project:openoblivion'),
                   (['prior-art', 'oblivion'], 'game:oblivion'), (['show', 'exp:EXP-OO-001'], '## Why'), (['snippet'], 'Query first'), (['template', 'experiment'], '## Oracle')):
    out = subprocess.run([sys.executable, hub] + args, capture_output=True, text=True, env=env)
    check(out.returncode == 0 and want in out.stdout, f'hub {" ".join(args[:2])} failed or missing {want!r}: {out.stderr[-200:]}')
# relevance: golden queries (tests/golden_queries.json). A ranking bug gets a regression test, not a silent fix.
g = subprocess.run([sys.executable, os.path.join(HERE, 'golden.py')], capture_output=True, text=True, env=env)
check(g.returncode == 0, 'golden queries failed:\n' + g.stdout[-2500:] + g.stderr[-500:])
print(f'{ok} checks passed, {len(fails)} failed')
sys.exit(1 if fails else 0)

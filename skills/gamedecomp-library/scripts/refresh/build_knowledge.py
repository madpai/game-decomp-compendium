#!/usr/bin/env python3
"""Build and validate everything generated from knowledge/: field notes (+gotchas), experiments, the research graph.

usage: build_knowledge.py [--repo-root DIR] [--check]

Reads   knowledge/**/*.md                (field notes)            -> data/local-notes.json, knowledge/INDEX.md
        knowledge/experiments/*.md       (experiments, dead ends) -> data/experiments.json, knowledge/experiments/INDEX.md
        knowledge/graph/{nodes,edges,findings}.jsonl              -> data/graph.json
Validates schemas, evidence levels, pointers (every source must resolve), cross references and orphans.
--check writes nothing and exits 1 when anything is invalid or a generated file is stale (CI and selftest use it).
Edit the sources, run this, commit both. Never edit data/graph.json or data/experiments.json by hand."""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import index_local_notes as notes_mod
import index_experiments as exp_mod
import rgraph


def read_jsonl(path, bad):
    out = []
    if not os.path.isfile(path): bad.append(f'{os.path.basename(path)} missing'); return out
    for n, line in enumerate(open(path, encoding='utf-8'), 1):
        s = line.strip()
        if not s or s.startswith('#'): continue
        try: out.append(json.loads(s))
        except ValueError as e: bad.append(f'{os.path.basename(path)}:{n}: invalid JSON ({e})')
    return out


def build(repo_root):
    bad = []
    data = os.path.join(repo_root, 'skills', 'gamedecomp-library', 'data')
    notes, b = notes_mod.collect(repo_root); bad += b
    exps, b = exp_mod.collect(repo_root); bad += b
    gd = os.path.join(repo_root, 'knowledge', 'graph')
    nodes = read_jsonl(os.path.join(gd, 'nodes.jsonl'), bad)
    edges = read_jsonl(os.path.join(gd, 'edges.jsonl'), bad)
    findings = read_jsonl(os.path.join(gd, 'findings.jsonl'), bad)
    catalog = json.load(open(os.path.join(data, 'catalog.json')))
    playbooks = json.load(open(os.path.join(data, 'playbooks.json')))['playbooks']
    ctx = {'repo_root': repo_root, 'exp_ids': {e['id'] for e in exps}, 'catalog_ids': {c['id'] for c in catalog},
           'playbook_ids': {p['id'] for p in playbooks}, 'finding_ids': {f.get('id') for f in findings}, 'exp_node_ids': ['exp:' + e['id'] for e in exps]}
    bad += rgraph.validate(nodes, edges, findings, ctx)
    ids = {n['id'] for n in nodes if 'id' in n}
    # experiments: cross references into the graph
    for e in exps:
        p = 'project:' + e['project']
        if p not in ids: bad.append(f"{e['path']}: project {e['project']!r} is not a node (project:{e['project']})")
        for a in list(e['about']) + list(e['games']):
            if a not in ids: bad.append(f"{e['path']}: about/games node {a!r} is not in knowledge/graph/nodes.jsonl")
    # derived nodes and edges
    gnodes = {}
    for n in nodes:
        if 'id' not in n: continue
        gnodes[n['id']] = {k: v for k, v in n.items() if k != 'id'}
    gedges = []
    for s, p, o, level, source, *rest in edges:
        if isinstance(s, str):
            gedges.append({'s': s, 'p': p, 'o': o, 'level': level, 'source': source, 'note': rest[0] if rest else ''})
    for f in findings:
        if 'id' not in f: continue
        gnodes[f['id']] = {'name': f['id'].split(':', 1)[1], 'summary': f.get('claim', ''), 'level': f.get('level'), 'scope': f.get('scope'), 'build': f.get('build', ''),
                           'oracle': f.get('oracle', ''), 'unverified': f.get('unverified', ''), 'source': f.get('source', []), 'confirmed_by': f.get('confirmed_by', []), 'note': f.get('note', '')}
        for a in f.get('about', []):
            gedges.append({'s': f['id'], 'p': 'about', 'o': a, 'level': f.get('level', 'guessed'), 'source': '; '.join(f.get('source', [])), 'note': ''})
    for e in exps:
        x = 'exp:' + e['id']
        gnodes[x] = {'name': e['title'], 'summary': re.sub(r'\s+', ' ', e['sections']['Symptom'])[:240], 'result': e['result'], 'level': e['level'], 'why_level': e['why_level'],
                     'scope': e['scope'], 'project': e['project']}
        gedges.append({'s': x, 'p': 'in_project', 'o': 'project:' + e['project'], 'level': e['level'], 'source': 'exp:' + e['id'], 'note': ''})
        for a in e['about']:
            gedges.append({'s': x, 'p': 'about', 'o': a, 'level': e['level'], 'source': 'exp:' + e['id'], 'note': ''})
        if e['supersedes']:
            gedges.append({'s': x, 'p': 'supersedes', 'o': 'exp:' + e['supersedes'], 'level': e['level'], 'source': 'exp:' + e['id'], 'note': ''})
    # a node nothing connects to is speculative; require a consumer
    touched = {x['s'] for x in gedges} | {x['o'] for x in gedges}
    for i in ids:
        if i not in touched: bad.append(f'orphan node {i}: no edge, finding or experiment mentions it')
    gedges.sort(key=lambda x: (x['s'], x['p'], x['o']))
    graph = {'meta': {'nodes': len(gnodes), 'edges': len(gedges), 'findings': len(findings), 'experiments': len(exps),
                      'note': 'generated by refresh/build_knowledge.py from knowledge/graph and knowledge/experiments'},
             'levels': rgraph.LEVELS, 'predicates': {p: {'domain': sorted(d), 'range': sorted(r) if len(r) < len(rgraph.NODE_TYPES) else ['any'], 'doc': t} for p, (d, r, t) in rgraph.PREDICATES.items()},
             'nodes': dict(sorted(gnodes.items())), 'edges': gedges}
    outs = {}
    ntargets = notes_mod.targets(repo_root); nout = notes_mod.render(notes)
    outs[ntargets['data']] = nout['data']; outs[ntargets['index']] = nout['index']
    outs[os.path.join(data, 'experiments.json')] = json.dumps({'meta': {'source': 'https://github.com/madpai/game-decomp-compendium', 'license': 'MIT'}, 'experiments': exps}, indent=0, ensure_ascii=False)
    outs[os.path.join(repo_root, 'knowledge', 'experiments', 'INDEX.md')] = exp_mod.render_index(exps)
    outs[os.path.join(data, 'graph.json')] = json.dumps(graph, indent=0, ensure_ascii=False, sort_keys=False)
    return outs, bad, {'notes': len(notes), 'experiments': len(exps), 'nodes': len(gnodes), 'edges': len(gedges), 'findings': len(findings)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo-root', default=os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    outs, bad, counts = build(a.repo_root)
    if a.check:
        for p, text in outs.items():
            if not os.path.isfile(p) or open(p, encoding='utf-8').read() != text: bad.append(f'{os.path.relpath(p, a.repo_root)} is out of date: run skills/gamedecomp-library/scripts/refresh/build_knowledge.py')
    elif not bad:
        for p, text in outs.items():
            os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(text)
    print(', '.join(f'{v} {k}' for k, v in counts.items()), ('\nPROBLEMS:\n  ' + '\n  '.join(bad)) if bad else '\nok' + ('' if a.check else ' (written)'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__': main()

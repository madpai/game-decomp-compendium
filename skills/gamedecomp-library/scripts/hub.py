#!/usr/bin/env python3
"""One front door to everything the compendium knows: decomp/tool projects, agent field notes and gotchas, experiments and
dead ends, findings with evidence levels, the research graph, engine playbooks, and the how-to references of the sibling skills.

  hub.py prior-art "oblivion"                         grouped answer: graph card, dead ends, findings, projects, notes, gotchas, playbook, refs
  hub.py diagnose "player shakes while walking upstairs"   symptom -> likely subsystems, prior incidents, causes, oracles, failed approaches, next steps
  hub.py tried "lua onFrame camera smoothing"         has this approach been tried? warns with the experiment id and why it failed
  hub.py search "MSVC RTTI vtable" [--source refs,notes,experiments,gotchas,findings,projects,playbooks,mskills]
  hub.py experiments [query] [--result failed] [--project openoblivion] [--about camera]
  hub.py graph show oblivion | find project --has msvc --has havok --has gamebryo --rel reverse_engineered:movement | path A B | stats | predicates
  hub.py show exp:EXP-OO-001 | finding:<id> | project:<id> | note:<path> | gotcha:<note>#<n> | ref:<skill>/<file> | node:<id or alias>
  hub.py template experiment|note|finding|edge        paste-ready record templates for writing knowledge back
  hub.py snippet                                      paste-ready instructions for a project that uses this compendium
  hub.py sources | where

Output always names where the full text lives; read only what the hit points to. Evidence levels: guessed < inferred < documented < static < verified.
Add --no-expand to search/prior-art to turn off graph-alias query expansion.
"""
import argparse, json, os, re, sys, textwrap
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import search_core as sc
from common import load, LOCAL_DATA, CACHE, REPO, CLONES, SKILLS_ROOT

TEMPLATES = os.path.normpath(os.path.join(HERE, '..', 'templates'))


def label(d):
    if d.kind == 'experiment':
        e = d.extra
        return ('!! ' if e['result'] in ('failed', 'partial') else '   ') + f"[experiment] {d.title}"
    return f"[{d.kind}] {d.title}"


def show_doc(d, q, mark_pointer=True):
    ptr = f"hub.py show {d.id}" if d.kind in ('experiment', 'finding', 'gotcha') else d.where
    if d.kind == 'experiment':
        e = d.extra
        print(f"{label(d)[:150]}\n    {d.meta}\n    why: {sc.first_sentences(e['sections']['Why'], 1, 170, 40)}\n    -> {ptr}")
    elif d.kind == 'gotcha':
        print(f"{label(d)[:150]}\n    cause: {d.extra['cause'][:160]}\n    -> {ptr}")
    elif d.kind == 'finding':
        print(f"[finding] {d.extra['summary'][:200]}{'…' if len(d.extra['summary']) > 200 else ''}\n    {d.meta}\n    -> {ptr}")
    else:
        print(f"{label(d)}\n    {d.meta}\n    {sc.snippet(d, q, 180)}\n    -> {ptr}")


def cmd_search(a):
    srcs = set((a.source or ','.join(sc.DEFAULT_SOURCES)).split(','))
    if 'all' in srcs: srcs = set(sc.DEFAULT_SOURCES)
    hits = sc.search(a.query, srcs, a.limit, a.full_text, not a.no_expand)
    for s, d in hits: show_doc(d, a.query); print()
    print(f"# {len(hits)} hit(s)", file=sys.stderr)


def print_card(c, g):
    print(f"[{c['id'].split(':')[0]}] {c['name']}  ({c['id']})\n    {c['summary']}")
    if c['facts']: print(f"    {c['facts']}")
    cat = None
    n = g.nodes[c['id']]
    if n.get('catalog'):
        cat = next((e for e in load('catalog.json') if e['id'] == n['catalog']), None)
    if cat: print(f"    catalog: {cat['id']} | ai policy: {cat['ai']} | {cat['license'] or '-'} | {cat['url']}")
    if n.get('url'): print(f"    url: {n['url']}")
    def names(ids, k=6): return ', '.join(g.title(i) if not i.startswith(('exp:', 'finding:')) else i.split(':', 1)[1] for i in ids[:k]) + (f' (+{len(ids) - k})' if len(ids) > k else '')
    if c['projects']: print(f"    projects linked to it: {names(sorted(set(c['projects'])))}")
    if c['problems']: print(f"    known problems: {names(sorted(set(c['problems'])))}")
    if c['techniques']: print(f"    techniques that apply: {names(c['techniques'])}")
    if c['experiments']:
        res = [f"{i.split(':', 1)[1]} ({g.nodes[i].get('result')})" for i in c['experiments']]
        print(f"    experiments: {', '.join(res[:8])}")
    if c['findings']: print(f"    findings: {', '.join(i.split(':', 1)[1] for i in c['findings'][:6])}")
    print(f"    -> hub.py graph show {c['id']}")


def cmd_prior_art(a):
    groups = sc.prior_art(a.query, a.per_group, a.full_text, not a.no_expand)
    print(f"Prior art for: {a.query}\n")
    g = sc.graph()
    if g:
        matched = sc.prior_art_entities(a.query)
        print("== Research graph: entities in your query" + ('' if matched else '  (none recognised)'))
        for i in matched: print_card(sc.card(i), g); print()
        if not matched: print()
    for kind, label_ in sc.GROUPS.items():
        hs = groups[kind]
        print(f"== {label_}" + ('' if hs else '  (nothing found)'))
        for s, d in hs: show_doc(d, a.query); print()
    if any(d.extra.get('result') in ('failed', 'partial') for s, d in groups['experiment']):
        print("!! A failed or partial experiment matched: read its Why and Next (`hub.py show exp:<ID>`) before repeating the idea.\n")
    print("Next: read the top hit of each group before searching the web; if nothing is found, say so and start with game-recon steps (engine, build, anti-cheat, loaders). Symptom first? `hub.py diagnose \"<symptom>\"`.")


def cmd_diagnose(a):
    import diagnose
    r = diagnose.diagnose(a.query, a.limit)
    if a.json: print(json.dumps(r, indent=1, ensure_ascii=False))
    else: print(diagnose.render(r))


def cmd_tried(a):
    hits = sc.tried(a.query, a.project, a.limit)
    print(f'Already-tried check for: "{a.query}"\n')
    if not hits:
        print("No recorded experiment matches. Absence of a record is not evidence that nobody tried it: check `hub.py prior-art` and the project's own docs, then record your attempt (`hub.py template experiment`).")
        return
    order = {'failed': 0, 'partial': 1, 'inconclusive': 2, 'worked': 3}
    for k, (s, d) in enumerate(sorted(hits, key=lambda h: (order[h[1].extra['result']], -h[0]))):
        e = d.extra; sec = e['sections']
        if k >= 3:
            print(f"   also: {e['id']} [{e['result']}, {e['project']}] {e['title']}   (hub.py show {d.id})")
            continue
        if e['result'] == 'failed':
            print(f"!! ALREADY TRIED in {e['project']} and it FAILED -> {e['id']}: {e['title']}")
            print(f"   tried: {sc.first_sentences(sec['Change'], 1, 260)}")
            print(f"   why it failed: {sc.first_sentences(sec['Why'], 2, 420)}")
            print(f"   instead: {sc.first_sentences(sec['Next'], 1, 300)}")
        elif e['result'] == 'partial':
            print(f"!! TRIED in {e['project']} with a PARTIAL result -> {e['id']}: {e['title']}")
            print(f"   what it established: {sc.first_sentences(sec['Result'], 1, 300)}")
            print(f"   why it fell short: {sc.first_sentences(sec['Why'], 2, 380)}")
            print(f"   next: {sc.first_sentences(sec['Next'], 1, 300)}")
        else:
            print(f"   related: {e['result']} in {e['project']} -> {e['id']}: {e['title']}")
            print(f"   what it established: {sc.first_sentences(sec['Result'], 1, 260)}")
            print(f"   still unverified: {sc.first_sentences(sec['Unverified'], 1, 220)}")
        print(f"   evidence: result {e['level']}, cause {e['why_level']}, scope {e['scope']}" + (f"; related: {', '.join(e['related'])}" if e['related'] else ''))
        print(f"   see: hub.py show {d.id}\n")


def cmd_experiments(a):
    exps = load('experiments.json', {'experiments': []})['experiments']
    g = sc.graph()
    if a.result: exps = [e for e in exps if e['result'] == a.result]
    if a.project: exps = [e for e in exps if e['project'] == a.project]
    if a.level: exps = [e for e in exps if e['level'] == a.level]
    if a.about and g:
        targets = set(g.resolve(a.about)); exps = [e for e in exps if targets & set(e['about'])]
    if a.query:
        docs = [d for d in sc.docs_for({'experiments'}) if d.extra['id'] in {e['id'] for e in exps}]
        ids = [d.extra['id'] for s, d in sc.rank(docs, a.query, 50, extra=sc.expansion(a.query), min_frac=0.34)]
        exps = [e for i in ids for e in exps if e['id'] == i]
    for e in exps:
        print(f"{'!!' if e['result'] in ('failed', 'partial') else '  '} {e['id']:<12} {e['result']:<12} {e['level']:<9}/{e['why_level']:<9} {e['project']:<14} {e['title']}")
    print(f"# {len(exps)} experiment(s); `hub.py show exp:<ID>` for the record", file=sys.stderr)


def print_experiment(e):
    print(f"{e['id']}  [{e['result']}]  {e['title']}\nproject: {e['project']} | scope: {e['scope']} | result evidence: {e['level']} | cause evidence: {e['why_level']} | date: {e['date']} | status: {e['status']}")
    print(f"about: {', '.join(e['about'])}" + (f" | related: {', '.join(e['related'])}" if e['related'] else '') + f"\nfull record: {e['url']}\n")
    for k, v in e['sections'].items(): print(f"## {k}\n{v}\n")


def print_finding(i, g):
    n = g.nodes[i]
    print(f"{i}\n  claim: {n['summary']}\n  evidence: {n['level']} | scope: {n['scope']}" + (f" | build: {n['build']}" if n.get('build') else ''))
    if n.get('oracle'): print(f"  oracle: {n['oracle']}")
    print(f"  unverified: {n['unverified']}\n  source: {', '.join(n['source'])}" + (f"\n  independently confirmed by: {', '.join(n['confirmed_by'])}" if n.get('confirmed_by') else ''))
    if n.get('note'): print(f"  note: {n['note']}")
    print('  about: ' + ', '.join(g.title(e['o']) for e in g.out.get(i, []) if e['p'] == 'about'))


def graph_show(g, term, show_all=False):
    ids = g.resolve(term)
    if not ids: sys.exit(f'no graph node matches {term!r}; try `hub.py graph find <type>` or `hub.py search`')
    for i in ids[:3]:
        if i.startswith('finding:'): print_finding(i, g); continue
        if i.startswith('exp:'): print_experiment(next(e for e in load('experiments.json')['experiments'] if 'exp:' + e['id'] == i)); continue
        n = g.nodes[i]
        print(f"{i}  {n['name']}\n  {n['summary']}")
        if n.get('aliases'): print(f"  aliases: {', '.join(n['aliases'])}")
        if n.get('url'): print(f"  url: {n['url']}")
        if n.get('catalog'):
            cat = next((e for e in load('catalog.json') if e['id'] == n['catalog']), None)
            if cat: print(f"  catalog: {cat['id']} (ai policy: {cat['ai']}, licence: {cat['license'] or '-'}, depth: {cat['depth']})")
        cap = 10**6 if show_all else 14
        def edge_line(e, other, arrow):
            s = e['source'] if len(e['source']) < 70 else e['source'][:67] + '...'
            return f"    {arrow} {e['p']}: {g.title(other)} ({other})  [{e['level']}]  {s}" + (f"\n        note: {e['note']}" if e.get('note') else '')
        outs = [e for e in g.out.get(i, []) if e['p'] not in ('about', 'in_project', 'supersedes')]
        if outs:
            print('  outgoing:')
            for e in outs[:cap]: print(edge_line(e, e['o'], '->'))
            if len(outs) > cap: print(f'    ... {len(outs) - cap} more (--all)')
        ins = [e for e in g.inn.get(i, []) if e['p'] not in ('about', 'in_project', 'supersedes')]
        if ins:
            print('  incoming:')
            for e in ins[:cap]: print(edge_line(e, e['s'], '<-'))
            if len(ins) > cap: print(f'    ... {len(ins) - cap} more (--all)')
        exps = [e['s'] for e in g.inn.get(i, []) if e['p'] == 'about' and e['s'].startswith('exp:')]
        fnds = [e['s'] for e in g.inn.get(i, []) if e['p'] == 'about' and e['s'].startswith('finding:')]
        if exps:
            print('  experiments about it:')
            for x in exps: print(f"    {x.split(':', 1)[1]} [{g.nodes[x].get('result')}; {g.nodes[x].get('level')}/{g.nodes[x].get('why_level')}] {g.nodes[x]['name']}")
        if fnds:
            print('  findings about it:')
            for x in fnds: print(f"    {x.split(':', 1)[1]} [{g.nodes[x].get('level')}, {g.nodes[x].get('scope')}] {g.nodes[x]['summary'][:150]}")
        print()


def cmd_graph(a):
    g = sc.graph()
    if not g: sys.exit('data/graph.json not found: run skills/gamedecomp-library/scripts/refresh/build_knowledge.py (or update the data cache)')
    import rgraph
    if a.gcmd == 'show': graph_show(g, a.term, a.all)
    elif a.gcmd == 'find':
        t = a.type.lower().rstrip('s') if a.type.lower() not in ('games',) else 'game'
        t = {'format': 'fmt', 'tool': 'technique'}.get(t, t)
        if t not in rgraph.NODE_TYPES: sys.exit(f'type must be one of {rgraph.NODE_TYPES}')
        res = g.find(t, a.has or [], a.rel or [], a.min_level)
        cats = {e['id']: e for e in load('catalog.json')} if t == 'project' else {}
        for i, ev in res:
            n = g.nodes[i]; c = cats.get(n.get('catalog'))
            print(f"{i}  {n['name']}" + (f"   [ai policy: {c['ai']}]" if c else ''))
            for line in ev: print(f"    {line}")
        print(f"# {len(res)} match(es) of {sum(1 for i in g.nodes if i.startswith(t + ':'))} {t} nodes. A missing edge means unknown, not no: the graph only holds what has been recorded.", file=sys.stderr)
    elif a.gcmd == 'path':
        p = g.path(a.a, a.b)
        if p is None: sys.exit('could not resolve one of the terms')
        if not p: print('no path within 6 hops (not related in the recorded graph)'); return
        for node, edge, arrow in p:
            print(f"{'   ' if edge is None else '  ' + arrow + ' ' + edge['p'] + ' [' + edge['level'] + '] '}{g.title(node)} ({node})")
    elif a.gcmd == 'stats':
        import collections
        print(f"nodes {len(g.nodes)}  edges {len(g.edges)}")
        print('node types:', dict(collections.Counter(i.split(':')[0] for i in g.nodes)))
        print('edge predicates:', dict(collections.Counter(e['p'] for e in g.edges).most_common()))
        print('edge levels (hand-written predicates only):', dict(collections.Counter(e['level'] for e in g.edges if e['p'] not in rgraph.DERIVED)))
        fl = [n for i, n in g.nodes.items() if i.startswith('finding:')]
        print('findings by level:', dict(collections.Counter(n['level'] for n in fl)), '| independently confirmed:', sum(1 for n in fl if n.get('confirmed_by')))
        ex = [n for i, n in g.nodes.items() if i.startswith('exp:')]
        print('experiments by result:', dict(collections.Counter(n['result'] for n in ex)))
    elif a.gcmd == 'predicates':
        print('Evidence levels (weakest to strongest; an ordering for filtering, not a probability):')
        for l in rgraph.LEVELS: print(f"  {l:<11} {rgraph.LEVEL_HELP[l]}")
        print('\nScopes:')
        for s in rgraph.SCOPES: print(f"  {s:<8} {rgraph.SCOPE_HELP[s]}")
        print('\nPredicates (subject types -> object types):')
        for p, (dom, rng, doc) in rgraph.PREDICATES.items():
            print(f"  {p:<19} {','.join(sorted(dom))} -> {','.join(sorted(rng)) if len(rng) < len(rgraph.NODE_TYPES) else 'any'}   {doc}{'  [derived]' if p in rgraph.DERIVED else ''}")
        print('\nPointers in `source`: ' + ' | '.join(rgraph.POINTERS))


def cmd_show(a):
    kind, _, ident = a.target.partition(':')
    if kind == 'project':
        for e in load('catalog.json'):
            if e['id'] == ident or ident in e['id']:
                print(json.dumps(e, indent=1, ensure_ascii=False)); return
    elif kind in ('note', 'playbook'):
        pool = (load('field-notes.json')['notes'] + load('local-notes.json', {'notes': []})['notes']) if kind == 'note' else load('playbooks.json')['playbooks']
        for e in pool:
            if ident in (e.get('path'), e.get('id')) or ident in e['path']:
                print(json.dumps({k: v for k, v in e.items() if k != 'gotcha_items'}, indent=1, ensure_ascii=False))
                lp = os.path.join(CLONES, 'universal-modder', 'knowledge' if kind == 'note' else '', e['path'] if kind == 'playbook' else e['path'])
                print(f"\nfull text: {e['url']}" + (f"\nlocal: {lp}" if os.path.isfile(lp) else ''))
                return
    elif kind == 'ref':
        p = os.path.join(SKILLS_ROOT, ident)
        if os.path.isfile(p): print(open(p, encoding='utf-8').read()); return
    elif kind == 'exp':
        for e in load('experiments.json', {'experiments': []})['experiments']:
            if e['id'] == ident: print_experiment(e); return
    elif kind in ('finding', 'node', 'game', 'engine', 'tech', 'compiler', 'platform', 'fmt', 'struct', 'subsystem', 'technique', 'approach', 'problem'):
        g = sc.graph()
        if g:
            graph_show(g, ident if kind == 'node' else a.target, True); return
    elif kind == 'gotcha':
        path, _, n = ident.partition('#')
        for src in ('local-notes.json',):
            for note in load(src, {'notes': []})['notes']:
                if note['path'] == path:
                    for it in note.get('gotcha_items', []):
                        if str(it['n']) == n:
                            print(f"{note['title']} :: gotcha {it['n']}\n  symptom: {it['symptom']}\n  cause: {it['cause'] or it.get('detail', '')}\n  fix: {it['fix']}\n  note: {note['url']}"); return
        lp = os.path.join(CLONES, 'universal-modder', 'knowledge', path)
        if os.path.isfile(lp):
            body = open(lp, encoding='utf-8').read()
            m = re.search(r'(?ms)^%s\.\s.*?(?=^\d+\.\s|^## |\Z)' % re.escape(n), body[body.find('## Gotchas'):])
            if m: print(m.group(0).rstrip()); print(f"\nnote: {sc.RAW + path}"); return
        for it in load('modder-gotchas.json', {'items': []})['items']:
            if it['note'] == path and str(it['n']) == n:
                print(f"gotcha {n} of {path}\n  symptom: {it['symptom']}\n  cause: {it['cause'] or it.get('detail', '')}\n  full text: {sc.RAW + path} (or clone universal-modder and re-run)"); return
    sys.exit(f'not found: {a.target}')


def cmd_template(a):
    names = {'experiment': 'experiment.md', 'note': 'note.md', 'finding': 'finding.jsonl', 'edge': 'edge.jsonl'}
    p = os.path.join(TEMPLATES, names[a.kind])
    if not os.path.isfile(p): sys.exit(f'template missing: {p}')
    print(open(p, encoding='utf-8').read())
    if a.kind in ('finding', 'edge'): print('# append one line to knowledge/graph/%ss.jsonl, then run refresh/build_knowledge.py' % a.kind)
    if a.kind == 'experiment': print('<!-- save as knowledge/experiments/exp-<project>-<nnn>-<slug>.md, then run refresh/build_knowledge.py and selftest.py -->')


def cmd_snippet(a):
    p = os.path.join(SKILLS_ROOT, 'gamedecomp-library', 'references', 'project-integration.md')
    if not os.path.isfile(p): sys.exit('references/project-integration.md not found')
    t = open(p, encoding='utf-8').read()
    m = re.search(r'<!-- snippet:start -->\n(.*?)<!-- snippet:end -->', t, re.S)
    print(m.group(1).rstrip() if m else t)


def cmd_sources(a):
    for s in load('sources.json')['sources']:
        print(f"{s['id']:<22} {s['kind']:<12} {s['license']:<14} {s['snapshot']:<11} {s['url']}\n    {s['use']}")


def cmd_where(a):
    print('local data :', LOCAL_DATA, '(exists)' if os.path.isdir(LOCAL_DATA) else '(missing)')
    print('cache      :', CACHE); print('clones     :', CLONES); print('skills root:', SKILLS_ROOT); print('repo       :', f'https://github.com/{REPO}')
    g = sc.graph()
    if g: print('graph      :', f'{len(g.nodes)} nodes, {len(g.edges)} edges, {sum(1 for i in g.nodes if i.startswith("exp:"))} experiments, {sum(1 for i in g.nodes if i.startswith("finding:"))} findings')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('search'); p.add_argument('query'); p.add_argument('--source'); p.add_argument('--limit', type=int, default=10); p.add_argument('--full-text', action='store_true'); p.add_argument('--no-expand', action='store_true'); p.set_defaults(fn=cmd_search)
    p = sub.add_parser('prior-art'); p.add_argument('query'); p.add_argument('--per-group', '--limit', dest='per_group', type=int, default=3); p.add_argument('--full-text', action='store_true'); p.add_argument('--no-expand', action='store_true'); p.set_defaults(fn=cmd_prior_art)
    p = sub.add_parser('diagnose'); p.add_argument('query'); p.add_argument('--limit', type=int, default=3); p.add_argument('--json', action='store_true'); p.set_defaults(fn=cmd_diagnose)
    p = sub.add_parser('tried'); p.add_argument('query'); p.add_argument('--project'); p.add_argument('--limit', type=int, default=4); p.set_defaults(fn=cmd_tried)
    p = sub.add_parser('experiments'); p.add_argument('query', nargs='?'); p.add_argument('--result', choices=['worked', 'failed', 'partial', 'inconclusive']); p.add_argument('--project'); p.add_argument('--level'); p.add_argument('--about'); p.set_defaults(fn=cmd_experiments)
    p = sub.add_parser('graph'); gs = p.add_subparsers(dest='gcmd', required=True); p.set_defaults(fn=cmd_graph)
    q = gs.add_parser('show'); q.add_argument('term'); q.add_argument('--all', action='store_true')
    q = gs.add_parser('find'); q.add_argument('type'); q.add_argument('--has', action='append'); q.add_argument('--rel', action='append', help='PRED:TERM, e.g. reverse_engineered:movement; PRED may be experiment or failed'); q.add_argument('--min-level', choices=['guessed', 'inferred', 'documented', 'static', 'verified'])
    q = gs.add_parser('path'); q.add_argument('a'); q.add_argument('b')
    gs.add_parser('stats'); gs.add_parser('predicates')
    p = sub.add_parser('show'); p.add_argument('target'); p.set_defaults(fn=cmd_show)
    p = sub.add_parser('template'); p.add_argument('kind', choices=['experiment', 'note', 'finding', 'edge']); p.set_defaults(fn=cmd_template)
    sub.add_parser('snippet').set_defaults(fn=cmd_snippet)
    sub.add_parser('sources').set_defaults(fn=cmd_sources); sub.add_parser('where').set_defaults(fn=cmd_where)
    a = ap.parse_args(); a.fn(a)

if __name__ == '__main__': main()

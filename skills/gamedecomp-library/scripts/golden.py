#!/usr/bin/env python3
"""Search-quality regression tests ("golden queries") for the compendium's retrieval.

  golden.py                      run every golden query, exit 1 on any failure
  golden.py -v                   also show where each expected item was found
  golden.py --stub search "query" [--source refs,notes]    print the top items and a JSON stub to paste into tests/golden_queries.json
  golden.py --stub diagnose "symptom" | prior-art "q" | tried "idea"

A test names a command, a query and expectations: `expect` items must appear within the first `top` items of a group
(or of the whole ranked list), `forbid` items must not. `any` is a list of substrings matched case-insensitively against
"<kind> <id> <title>". Windows are deliberately wide (top 3-8) so benign reranking does not break them.

WHEN YOU FIND A RANKING BUG: fix it if you can, and ALWAYS add a regression test (give it `regression` text saying what went
wrong and when). Do not fix silently. Structural checks live in selftest.py; this file checks relevance.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import search_core as sc
GOLDEN = os.path.normpath(os.path.join(HERE, '..', 'tests', 'golden_queries.json'))


def lower(*parts):
    return ' '.join(str(p) for p in parts if p).lower()


def run_command(t):
    """Return {group: [text, ...]} (ranked) for one test, or a group '*' with all items in order for the unfiltered window."""
    cmd, q = t['cmd'], t.get('query', '')
    out = {}
    if cmd == 'search':
        srcs = set(t['source'].split(',')) if t.get('source') else None
        hits = sc.search(q, srcs, t.get('limit', 30), False, not t.get('no_expand', False))
        out['*'] = [lower(d.kind, d.id, d.title) for s, d in hits]
        for s, d in hits: out.setdefault(d.kind, []).append(lower(d.kind, d.id, d.title))
    elif cmd == 'prior-art':
        pa = sc.prior_art(q, per_group=t.get('per_group', 8))
        for k, hs in pa.items(): out[k] = [lower(d.kind, d.id, d.title) for s, d in hs]
        out['entity'] = [lower(i) for i in sc.prior_art_entities(q, 5)]
        out['*'] = [x for k in pa for x in out[k]]
    elif cmd == 'diagnose':
        import diagnose
        r = diagnose.diagnose(q, t.get('limit', 5))
        out['subsystems'] = [lower(x['id'], x['name']) for x in r['subsystems']]
        out['problems'] = [lower(x['id'], x['name']) for x in r['problems']]
        out['incidents'] = [lower(x['id'], x['title'], x['result']) for x in r['incidents']]
        out['causes'] = [lower(x['id'], x['symptom'], x['cause']) for x in r['causes']]
        out['failed'] = [lower(x['id'], x['title']) for x in r['failed']]
        out['oracles'] = [lower(x['id'], x['oracle']) for x in r['oracles']]
        out['techniques'] = [lower(x['id'], x['name']) for x in r['techniques']]
        out['facts'] = [lower(x['id'], x['claim']) for x in r['facts']]
        out['next'] = [lower(x['id'], x['step']) for x in r['next']]
        out['read'] = [lower(x['id'], x['title']) for x in r['read']]
        out['*'] = [x for k, v in out.items() for x in v]
    elif cmd == 'tried':
        hits = sc.tried(q, t.get('project'), t.get('limit', 4))
        out['*'] = out['tried'] = [lower(d.id, d.title, d.extra['result']) for s, d in hits]
    elif cmd == 'graph-find':
        import rgraph
        g = sc.graph()
        res = g.find(t['type'], t.get('has', []), t.get('rel', []), t.get('min_level'))
        out['*'] = out['node'] = [lower(i) for i, ev in res]
    else:
        raise SystemExit(f'unknown golden cmd {cmd}')
    return out


def check(t, verbose=False):
    errs, notes = [], []
    groups = run_command(t)
    if t.get('expect_empty'):
        if groups.get('*'): errs.append(f"expected no results, got {groups['*'][:3]}")
        return errs, notes
    for kind, exps in (('expect', t.get('expect', [])), ('forbid', t.get('forbid', []))):
        for e in exps:
            items = groups.get(e.get('group', '*'), [])[:e.get('top', 5)]
            hit = next((i for i, text in enumerate(items, 1) if any(a.lower() in text for a in e['any'])), None)
            label = f"{e.get('group', '*')} top {e.get('top', 5)} any {e['any']}"
            if kind == 'expect':
                if hit is None: errs.append(f"missing: {label}; got {[x[:60] for x in items[:5]]}")
                elif verbose: notes.append(f"found at {hit}: {label}")
            elif hit is not None: errs.append(f"unwanted item at {hit} ({items[hit - 1][:70]}): {label}")
    return errs, notes


def run(verbose=False, only=None):
    tests = json.load(open(GOLDEN))['tests']
    fails, ok = [], 0
    for t in tests:
        if only and only not in t['id']: continue
        errs, notes = check(t, verbose)
        if errs:
            fails.append((t['id'], errs, t))
        else: ok += 1
        if verbose:
            print(('FAIL ' if errs else 'ok   ') + t['id'])
            for n in notes: print('       ' + n)
    return ok, fails


def stub(cmd, query, source=None):
    t = {'cmd': cmd, 'query': query}
    if source: t['source'] = source
    groups = run_command(t)
    print(f'# top items for {cmd} "{query}"')
    for g, items in groups.items():
        if g == '*': continue
        print(f'  [{g}]')
        for i, x in enumerate(items[:6], 1): print(f'    {i}. {x[:110]}')
    print('\n# paste into tests/golden_queries.json (edit `any` to the substrings that must appear, choose a wide `top`):')
    print(json.dumps({'id': 'short-id', 'cmd': cmd, 'query': query, 'expect': [{'group': '*', 'any': ['substring'], 'top': 5}], 'why': 'what an agent should find', 'added': '2026-01-01'}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-v', '--verbose', action='store_true'); ap.add_argument('--only')
    ap.add_argument('--stub', nargs=2, metavar=('CMD', 'QUERY')); ap.add_argument('--source')
    a = ap.parse_args()
    if a.stub: stub(a.stub[0], a.stub[1], a.source); return
    ok, fails = run(a.verbose, a.only)
    for tid, errs, t in fails:
        print(f'FAIL {tid}: {t["cmd"]} {t.get("query", "")!r}')
        for e in errs: print('   ' + e)
        if t.get('why'): print('   why this test exists: ' + t['why'])
    print(f'golden queries: {ok} passed, {len(fails)} failed')
    sys.exit(1 if fails else 0)


if __name__ == '__main__': main()

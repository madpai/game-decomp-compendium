"""Problem-first retrieval: from a symptom to likely subsystems, prior incidents, known causes, oracles, dead ends and next steps.

This is retrieval, not diagnosis. The subsystem guess comes from cue words attached to graph nodes (knowledge/graph/nodes.jsonl);
every other line is an existing record (experiment, gotcha, finding, reference) ranked by text overlap and graph links.
Each item carries its evidence level so the reader can discount weak ones.
"""
import collections, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import search_core as sc
import rgraph

DIAG_SOURCES = ('experiments', 'gotchas', 'findings', 'notes', 'refs')


def _tokens(text):
    return re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', (text or '').lower())


def _cue_hit(cue, qtoks, qtext):
    c = cue.lower()
    if ' ' in c or '-' in c:
        return f' {rgraph.norm(c)} ' in f' {rgraph.norm(qtext)} '
    for t in qtoks:
        if t == c: return True
        if len(c) >= 4 and len(t) >= 4 and (t.startswith(c) or c.startswith(t)) and abs(len(t) - len(c)) <= 3: return True
        if re.fullmatch(r'(up|down|over|under)' + re.escape(c), t): return True
    return False


def score_nodes(g, query):
    """Cue/alias scoring of subsystem and problem nodes. Cues shared by many nodes weigh less."""
    qtoks = _tokens(query)
    cands = [i for i, n in g.nodes.items() if rgraph.node_type(i) in ('subsystem', 'problem') and (n.get('cues') or n.get('aliases'))]
    df = collections.Counter(c.lower() for i in cands for c in set(g.nodes[i].get('cues', [])))
    out = []
    for i in cands:
        n = g.nodes[i]; s = 0.0; fired = []
        for c in n.get('cues', []):
            if _cue_hit(c, qtoks, query):
                s += 1.0 / math.sqrt(df[c.lower()]); fired.append(c)
        for a in n.get('aliases', []):
            if len(a) > 3 and _cue_hit(a, qtoks, query) and a not in fired:
                s += 1.5; fired.append(a)
        if s > 0: out.append((s, i, fired))
    out.sort(key=lambda x: (-x[0], x[1]))
    return out


def diagnose(query, limit=5):
    g = sc.graph()
    res = {'query': query, 'subsystems': [], 'problems': [], 'incidents': [], 'causes': [], 'failed': [], 'oracles': [], 'facts': [], 'next': [], 'read': [], 'techniques': []}
    scored = score_nodes(g, query) if g else []
    def strong(items):
        items = items[:3]
        return [x for x in items if x[0] >= 0.15 * items[0][0]] if items else []
    subs = strong([(s, i, f) for s, i, f in scored if i.startswith('subsystem:')])
    probs = strong([(s, i, f) for s, i, f in scored if i.startswith('problem:')])
    top_ids = {i for _, i, _ in subs + probs}
    for s, i, f in subs: res['subsystems'].append({'id': i, 'name': g.title(i), 'score': round(s, 2), 'cues': f, 'summary': g.nodes[i]['summary']})
    for s, i, f in probs: res['problems'].append({'id': i, 'name': g.title(i), 'score': round(s, 2), 'cues': f, 'summary': g.nodes[i]['summary']})
    # expansion: names and aliases of the strongest nodes, at lower weight
    extra = []
    for _, i, _ in (subs[:2] + probs[:1]):
        n = g.nodes[i]
        for t in sc.toks(n['name'] + ' ' + ' '.join(n.get('aliases', [])[:4])):
            extra.append(((t,), 0.6))
    extra += sc.expansion(query)
    docs = sc.docs_for(DIAG_SOURCES)
    own = [d for d in docs if d.kind in ('experiment', 'finding')]
    rest = [d for d in docs if d.kind not in ('experiment', 'finding')]
    hits = sc.rank(own, query, 60, extra=extra, min_frac=0.2, detail=True) + sc.rank(rest, query, 60, extra=extra, min_frac=0.4, detail=True)
    hits.sort(key=lambda x: -x[0])
    top = hits[0][0] if hits else 1.0
    nraw = {d.id: m for s, d, m in hits}
    scores = {d.id: s / top for s, d, m in hits}
    byid = {d.id: d for d in docs}
    # graph links: experiments and findings about the strongest nodes join even when words do not overlap
    linked = collections.defaultdict(float)
    if g:
        for nid in top_ids:
            for e in g.inn.get(nid, []):
                if e['p'] == 'about' and e['s'].split(':', 1)[0] in ('exp', 'finding'):
                    linked[e['s'] if e['s'].startswith('finding:') else e['s']] += 0.35
    comb = collections.defaultdict(float)
    for did, s in scores.items():
        if did in linked or nraw.get(did, 0) >= 2 or byid[did].kind in ('gotcha', 'ref', 'note'): comb[did] += s   # a lone shared word is not evidence
    for did, s in linked.items():
        if did in byid: comb[did] += s
    ranked = sorted(comb.items(), key=lambda x: -x[1])

    def pick(kind, n):
        return [byid[d] for d, s in ranked if byid[d].kind == kind and s >= 0.12][:n]
    exps = pick('experiment', limit)
    for d in exps:
        e = d.extra
        res['incidents'].append({'id': d.id, 'title': e['title'], 'project': e['project'], 'result': e['result'], 'level': e['level'], 'why_level': e['why_level'], 'scope': e['scope'],
                                 'symptom': sc.first_sentences(e['sections']['Symptom'], 1, 150, 40)})
    for d in sorted(exps, key=lambda d: 0 if d.extra['result'] in ('failed', 'partial') else 1):
        e = d.extra
        if e['result'] in ('failed', 'partial'):
            res['failed'].append({'id': d.id, 'title': e['title'], 'project': e['project'], 'result': e['result'], 'tried': sc.first_sentences(e['sections']['Change'], 1, 160),
                                  'why': sc.first_sentences(e['sections']['Why'], 2, 300), 'why_level': e['why_level'], 'next': sc.first_sentences(e['sections']['Next'], 1, 220)})
    failed_ids = {f['id'] for f in res['failed']}
    for d in exps:
        e = d.extra
        if d.id in failed_ids: continue          # its cause is already shown under failed approaches
        res['causes'].append({'id': d.id, 'from': 'experiment', 'symptom': e['title'], 'cause': sc.first_sentences(e['sections']['Why'], 1, 220), 'level': e['why_level'], 'result': e['result']})
    for d in pick('gotcha', limit):
        x = d.extra
        res['causes'].append({'id': d.id, 'from': 'gotcha (' + x['source'] + ')', 'symptom': x['symptom'], 'cause': (x['cause'] or '(no cause recorded; read the note)')[:200], 'level': '', 'result': ''})
    seen = set()
    for d in exps:
        o = sc.first_sentences(d.extra['sections']['Oracle'], 1, 170, 40)
        if o not in seen: seen.add(o); res['oracles'].append({'id': d.id, 'oracle': o})
    for d in pick('finding', limit):
        n = d.extra
        res['facts'].append({'id': d.id, 'claim': n['summary'], 'level': n.get('level'), 'scope': n.get('scope'), 'confirmed': bool(n.get('confirmed_by')), 'unverified': sc.first_sentences(n.get('unverified', ''), 1, 120, 30)})
    nseen = set()
    for d in sorted(exps, key=lambda d: 0 if d.extra['result'] in ('failed', 'partial') else 1):
        nx = sc.first_sentences(d.extra['sections']['Next'], 1, 200)
        if nx not in nseen: nseen.add(nx); res['next'].append({'id': d.id, 'step': nx})
    if g:
        for _, i, _ in subs[:2] + probs[:2]:
            for e in g.inn.get(i, []):
                if e['p'] in ('applies_to',) and e['s'].startswith('technique:'):
                    res['techniques'].append({'id': e['s'], 'name': g.title(e['s']), 'level': e['level'], 'summary': g.nodes[e['s']]['summary']})
    for d in [byid[x] for x, s in ranked if byid[x].kind in ('ref', 'note') and s >= 0.12][:4]:
        res['read'].append({'id': d.id, 'title': d.title[:110], 'where': d.where})
    # dedupe techniques
    seen = set(); res['techniques'] = [t for t in res['techniques'] if not (t['id'] in seen or seen.add(t['id']))]
    res['empty'] = not (res['incidents'] or res['causes'] or res['facts'] or res['subsystems'])
    return res


def render(r, cap=None):
    L = [f'Diagnose (retrieval over recorded evidence, not an expert system): {r["query"]}', '']
    if r['empty']:
        L += ['Nothing matched: no cue word hit a known subsystem and no record overlaps. Absence of a record is not evidence that nobody has seen this.',
              'Generic start: state the symptom as an observation with a metric, build an oracle first (references/agent-method.md), then `hub.py prior-art "<game or engine>"`.']
        return '\n'.join(L)
    L.append('== Likely subsystems (cue words matched; a guess to test, not a finding)')
    for s in r['subsystems']: L.append(f"  {s['id']:<32} {s['name']}  [cues: {', '.join(s['cues'][:5])}]")
    for s in r['problems']: L.append(f"  known problem pattern: {s['id']}  {s['name']}  [cues: {', '.join(s['cues'][:5])}]")
    if not r['subsystems'] and not r['problems']: L.append('  (no cue matched; evidence below is text overlap only)')
    L += ['', '== Prior incidents (experiments; the project, what happened, evidence level of result / cause)']
    for e in r['incidents']:
        flag = '!!' if e['result'] in ('failed', 'partial') else '  '
        L.append(f"{flag} {e['id']} [{e['result']}; {e['level']}/{e['why_level']}; {e['project']}] {e['title'][:100]}\n      symptom: {e['symptom']}")
    if not r['incidents']: L.append('  (none recorded)')
    L += ['', '== Known causes (symptom -> cause, with source and evidence level)']
    for c in r['causes']:
        lv = f" [{c['level']}]" if c['level'] else ''
        L.append(f"  {c['symptom'][:100]}\n      cause{lv}: {c['cause']}   ({c['id']})")
    if not r['causes']: L.append('  (none recorded)')
    L += ['', '== Failed approaches (do not repeat before reading why)']
    for f in r['failed']:
        L.append(f"!! {f['id']} [{f['result']}, {f['project']}] tried: {f['tried']}\n      why it failed [{f['why_level']}]: {f['why']}\n      instead: {f['next']}")
    if not r['failed']: L.append('  (no failed or partial experiment matched; that does not mean the idea is untried)')
    L += ['', '== Tests and oracles used before']
    for o in r['oracles']: L.append(f"  {o['id']}: {o['oracle']}")
    for t in r['techniques']: L.append(f"  technique {t['id']} [{t['level']}]: {t['summary']}")
    if not r['oracles'] and not r['techniques']: L.append('  (none recorded: define one before changing anything)')
    L += ['', '== Facts on record (evidence level, scope; what is still unverified)']
    for f in r['facts']:
        L.append(f"  [{f['level']}, {f['scope']}{', confirmed' if f['confirmed'] else ''}] {f['claim'][:230]}{'…' if len(f['claim']) > 230 else ''}   ({f['id']})")
    if not r['facts']: L.append('  (none)')
    L += ['', '== Recommended next steps (taken from the matching records)']
    for i, n in enumerate(r['next'], 1): L.append(f"  {i}. {n['step']}   ({n['id']})")
    for d in r['read']: L.append(f"  read: {d['title']}")
    if not r['next'] and not r['read']: L.append('  (no recorded next step: start with a measurement and an oracle)')
    L += ['', '`hub.py show <id>` opens a record (oracle, what is unverified). Discount inferred/guessed items; scope "project" is one project\'s choice, not an engine fact.']
    return '\n'.join(L)

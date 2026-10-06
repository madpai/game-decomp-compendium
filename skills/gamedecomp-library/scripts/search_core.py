"""Search engine shared by hub.py, diagnose.py and golden.py: build documents from every source, rank with a small BM25,
expand queries through the research graph's aliases. No dependencies; everything loads from data/*.json and the sibling
skills' reference files, so an installed skill needs no repository.

Document kinds: project, note, playbook, mskill, ref, experiment, gotcha, finding.
"""
import collections, functools, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, LOCAL_DATA, CACHE, REPO, CLONES, SKILLS_ROOT

STOP = set('a an and are as at be by for from has have how i in is it of on or that the this to was what when where which with you your do does did can could should would not no if then than into out up use used using get set new game games'.split())
DEFAULT_SOURCES = ('projects', 'notes', 'playbooks', 'mskills', 'refs', 'experiments', 'gotchas', 'findings')
RAW = 'https://github.com/rehan-remade/universal-modder/blob/main/knowledge/'


def toks(text):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9_.+#-]*", (text or '').lower().replace('--', ' ')) if t not in STOP and len(t) > 1]


class Doc:
    __slots__ = ('kind', 'id', 'title', 'text', 'weighted', 'where', 'meta', 'tf', 'len', 'extra')

    def __init__(self, kind, id, title, text, weighted, where, meta='', extra=None):
        self.kind, self.id, self.title, self.text, self.where, self.meta, self.extra = kind, id, title, text, where, meta, extra or {}
        words = toks(weighted) * 3 + toks(text)
        self.tf = collections.Counter(words); self.len = len(words) or 1


def graph():
    """The research graph, or None when data/graph.json is absent (older installs)."""
    try:
        import rgraph
        return rgraph.load_graph()
    except (SystemExit, FileNotFoundError, KeyError):
        return None


graph = functools.lru_cache(maxsize=1)(graph)


def first_sentences(text, n=1, limit=300, min_len=70):
    """The first n sentences (more if they are very short), clipped to limit characters."""
    t = re.sub(r'\s+', ' ', text or '').strip()
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z`(])', t)
    k = n
    while k < min(len(parts), n + 2) and len(' '.join(parts[:k])) < min_len: k += 1
    out = ' '.join(parts[:k])
    return out if len(out) <= limit else out[:limit - 1].rstrip() + '…'


def build_docs(sources, full_text=False):
    docs = []
    if 'projects' in sources:
        for e in load('catalog.json'):
            txt = ' '.join(filter(None, [e['summary'], e['note'], e['type'], e['platform'], ' '.join(e['tools']), ' '.join(e['compilers']), e['language'] or '']))
            meta = f"{e['category']} | {e['platform']} | {('%.0f%%' % e['progress']) if e['progress'] not in (None, '') else '-'} | {e['license'] or '-'} | ai:{e['ai']} | depth:{e['depth']}"
            docs.append(Doc('project', e['id'], e['name'], txt, e['name'] + ' ' + e['id'], e['url'], meta))
    notes = None
    if 'notes' in sources or 'gotchas' in sources:
        notes = load('field-notes.json', {'notes': []})['notes'] + load('local-notes.json', {'notes': []})['notes']
    if 'notes' in sources:
        for n in notes:
            body = ''
            if full_text:
                p = os.path.join(CLONES, 'universal-modder', 'knowledge', n['path'])
                if n.get('source') == 'local': p = os.path.join(SKILLS_ROOT, '..', 'knowledge', n['path'])
                if os.path.isfile(p): body = open(p, encoding='utf-8').read()
            txt = ' '.join([n.get('summary', ''), ' '.join(n.get('tags') or []), ' '.join(n.get('tools') or []), n.get('engine') or '', n.get('route') or '', n.get('anti_cheat') or '', n.get('verification') or '', body])
            docs.append(Doc('note', n['path'], n['title'], txt, f"{n['title']} {n.get('game','')} {' '.join(n.get('games_also') or [])} {' '.join(n.get('tags') or [])}", n['url'],
                            f"{n['kind']}{' (this repo)' if n.get('source') == 'local' else ' (universal-modder)'} | engine:{n.get('engine')} | route:{n.get('route')} | status:{n.get('status')} | gotchas:{n.get('gotchas')}"))
    if 'playbooks' in sources:
        for p in load('playbooks.json', {'playbooks': []})['playbooks']:
            docs.append(Doc('playbook', p['id'], p['title'], p['identify'] + ' ' + ' '.join(p['headings']), p['title'] + ' ' + p['id'], p['url'], 'engine playbook (universal-modder)'))
    if 'mskills' in sources:
        for s in load('modder-skills.json', {'skills': []})['skills']:
            docs.append(Doc('mskill', s['name'], s['name'], s['description'], s['name'], s['url'], 'universal-modder skill'))
    if 'refs' in sources and os.path.isdir(SKILLS_ROOT):
        for skill in sorted(os.listdir(SKILLS_ROOT)):
            sd = os.path.join(SKILLS_ROOT, skill)
            if not os.path.isdir(sd) or skill == 'synced': continue
            files = [os.path.join(sd, 'SKILL.md')] + [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(sd, 'references')) for f in fs if f.endswith('.md')]
            for fp in files:
                if not os.path.isfile(fp): continue
                rel = os.path.relpath(fp, SKILLS_ROOT)
                text = open(fp, encoding='utf-8').read()
                parts = re.split(r'(?m)^(#{1,3} .+)$', text)
                head = rel
                buf = parts[0]
                for i in range(1, len(parts), 2):
                    if buf.strip(): docs.append(Doc('ref', f'{rel}#{head}', f'{rel} :: {head}'.replace('# ', ''), buf, head, fp, 'skill reference'))
                    head, buf = parts[i].strip('# ').strip(), parts[i + 1]
                if buf.strip(): docs.append(Doc('ref', f'{rel}#{head}', f'{rel} :: {head}', buf, head, fp, 'skill reference'))
    g = graph() if ({'experiments', 'findings'} & set(sources)) else None
    if 'experiments' in sources:
        for e in load('experiments.json', {'experiments': []})['experiments']:
            s = e['sections']
            about = ' '.join(g.title(a) for a in e['about']) if g else ' '.join(e['about'])
            txt = ' '.join([s['Symptom'], s['Hypothesis'], s['Change'], s['Result'], s['Why'], s['Next'], s['Environment']])
            docs.append(Doc('experiment', 'exp:' + e['id'], f"{e['id']} [{e['result']}] {e['title']}", txt + ' ' + about, f"{e['title']} {e['id']} {e['project']} {' '.join(e['tags'])}", e['url'],
                            f"experiment | {e['project']} | result:{e['result']} ({e['level']}) | why:{e['why_level']} | scope:{e['scope']}", extra=e))
    if 'gotchas' in sources:
        titles = {n['path']: n['title'] for n in (notes or [])}
        for n in load('local-notes.json', {'notes': []})['notes']:
            for it in n.get('gotcha_items', []):
                docs.append(Doc('gotcha', f"gotcha:{n['path']}#{it['n']}", f"{n['title']} :: gotcha {it['n']}: {it['symptom']}", ' '.join([it['cause'], it['fix'], it.get('detail', '')]), it['symptom'], n['url'],
                                'gotcha (this repo)', extra={'note': n['path'], 'n': it['n'], 'symptom': it['symptom'], 'cause': it['cause'] or it.get('detail', ''), 'fix': it['fix'], 'source': 'local'}))
        for it in load('modder-gotchas.json', {'items': []})['items']:
            t = titles.get(it['note'], it['note'])
            docs.append(Doc('gotcha', f"gotcha:{it['note']}#{it['n']}", f"{t} :: gotcha {it['n']}: {it['symptom']}", ' '.join([it['cause'], it.get('detail', '')]), it['symptom'], RAW + it['note'],
                            'gotcha (universal-modder)', extra={'note': it['note'], 'n': it['n'], 'symptom': it['symptom'], 'cause': it['cause'] or it.get('detail', ''), 'fix': '', 'source': 'upstream'}))
    if 'findings' in sources and g:
        for i, n in g.nodes.items():
            if not i.startswith('finding:'): continue
            about = ' '.join(g.title(e['o']) for e in g.out.get(i, []) if e['p'] == 'about')
            docs.append(Doc('finding', i, n['summary'][:110], ' '.join([n['summary'], n.get('build', ''), n.get('oracle', ''), n.get('unverified', ''), about]), n['name'].replace('-', ' '), ', '.join(n.get('source', [])),
                            f"finding | {n.get('level')} | scope:{n.get('scope')}" + (' | independently confirmed' if n.get('confirmed_by') else ''), extra=n))
    return docs


_cache = {}
def docs_for(sources, full_text=False):
    key = (tuple(sorted(sources)), full_text)
    if key not in _cache: _cache[key] = build_docs(set(sources), full_text)
    return _cache[key]


def expansion(query, max_terms=8):
    """Extra (phrase, weight) pairs from the names and aliases of graph nodes mentioned in the query ('n64' -> the phrase
    'nintendo 64'). A phrase only scores on a document that contains ALL of its words, so 'nintendo 64' does not pull in 3DS games."""
    g = graph()
    if not g: return []
    q = set(toks(query)); out = []; seen = set()
    for alias, ids in g.match_text(query):
        for i in ids:
            n = g.nodes[i]
            for src in [n['name']] + list(n.get('aliases', [])):
                ph = tuple(toks(src))
                if ph and not set(ph) <= q and ph not in seen:
                    seen.add(ph); out.append((ph, 0.5))
    return out[:max_terms]


def rank(docs, query, limit, extra=None, min_frac=0.5, detail=False):
    """BM25 over docs. A hit must match at least `min_frac` of the distinct query terms. `extra` holds (phrase, weight) pairs
    (a bare string is a one-word phrase): they add score when every word of the phrase is present and may stand in for one
    missing query term, but never replace all of them."""
    q = toks(query)
    if not q: return []
    qset = set(q)
    extra = [((e[0],) if isinstance(e[0], str) else tuple(e[0]), e[1]) for e in (extra or [])]
    extra = [(ph, w) for ph, w in extra if not set(ph) <= qset]
    n = len(docs); avg = sum(d.len for d in docs) / max(n, 1)
    df = collections.Counter(t for d in docs for t in set(d.tf))
    res = []
    need = max(1, math.ceil(len(set(q)) * min_frac))

    def bm25(d, t, f, w):
        idf = math.log(1 + (n - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5))
        return w * idf * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * d.len / avg))
    for d in docs:
        score = 0.0; matched = set(); ematched = 0
        for t in q:
            f = d.tf.get(t, 0)
            if not f:
                f = sum(c for x, c in d.tf.items() if len(t) > 3 and (x.startswith(t) or t.startswith(x) and len(x) > 4)) * 0.5
            if not f: continue
            matched.add(t); score += bm25(d, t, f, 1.0)
        for ph, w in extra:
            if all(d.tf.get(x) for x in ph):
                ematched += 1
                for x in ph:
                    if x not in qset: score += bm25(d, x, d.tf[x], w)
        if score > 0 and len(matched) + min(ematched, 1) >= need and matched: res.append((score, d, len(matched)) if detail else (score, d))
    res.sort(key=lambda x: -x[0])
    return res[:limit]


def snippet(d, q, width=220):
    t = re.sub(r'\s+', ' ', d.text)
    for w in toks(q):
        i = t.lower().find(w)
        if i >= 0:
            s = max(0, i - 60); return ('…' if s else '') + t[s:s + width] + ('…' if s + width < len(t) else '')
    return t[:width]


def diversify(hits, limit, cap):
    """First `limit` hits with at most `cap` of any one kind; later hits of a capped kind fill the rest. Keeps one kind of short,
    keyword-dense record (findings, gotchas) from burying the skills and notes that are the entry points."""
    out, held, n = [], [], collections.Counter()
    for h in hits:
        k = h[1].kind
        if n[k] < cap: out.append(h); n[k] += 1
        else: held.append(h)
        if len(out) >= limit: break
    return (out + held)[:limit]


def search(query, sources=None, limit=10, full_text=False, expand=True):
    srcs = sources or DEFAULT_SOURCES
    docs = docs_for(srcs, full_text)
    hits = rank(docs, query, limit * 6, extra=expansion(query) if expand else None)
    return diversify(hits, limit, max(3, limit // 3 + 1)) if len(set(srcs)) > 1 else hits[:limit]


GROUPS = collections.OrderedDict([
    ('experiment', 'Experiments and dead ends (what was tried here before; failed ones first)'),
    ('finding', 'Findings (atomic claims with evidence level and scope)'),
    ('project', 'Decompilation / tool projects'),
    ('note', 'Agent field notes (what others learned doing it)'),
    ('gotcha', 'Gotchas (symptom -> cause)'),
    ('playbook', 'Engine playbooks'),
    ('ref', 'Sections of the installed skills (methods, formats, engine facts)')])
GROUP_LIMIT = {'gotcha': 3, 'finding': 4}


def graph_boost(hits, query):
    """Projects the graph connects to what the query names (an approach, platform, engine, game...) rank above text-only matches."""
    g = graph()
    if not g: return hits
    named = {i for _, ids in g.match_text(query) for i in ids if i.split(':', 1)[0] not in ('exp', 'finding')}
    if not named: return hits
    by_catalog = {n['catalog']: i for i, n in g.nodes.items() if n.get('catalog')}
    out = []
    for s, d in hits:
        nid = by_catalog.get(d.id) if d.kind == 'project' else None
        if nid:
            k = len(named & set(g.reach(nid, 3)))
            s = s * (1 + 0.6 * k)
        out.append((s, d))
    out.sort(key=lambda x: -x[0])
    return out


def prior_art(query, per_group=5, full_text=False, expand=True):
    docs = docs_for(DEFAULT_SOURCES, full_text)
    allhits = rank(docs, query, 600, extra=expansion(query) if expand else None)
    allhits = graph_boost(allhits, query) if expand else allhits
    out = collections.OrderedDict()
    for kind in GROUPS:
        hs = [(s, d) for s, d in allhits if d.kind == kind]
        if kind == 'experiment':     # failed and partial first: a dead end is the most expensive thing to rediscover
            hs.sort(key=lambda x: (0 if x[1].extra.get('result') in ('failed', 'partial') else 1, -x[0]))
        out[kind] = hs[:GROUP_LIMIT.get(kind, per_group)]
    return out


def card(node_id):
    """A compact entity card for a graph node: key facts, related projects, experiments, findings."""
    g = graph()
    n = g.nodes[node_id]
    c = {'id': node_id, 'name': n['name'], 'summary': n['summary'], 'facts': g.summary_line(node_id), 'projects': [], 'experiments': [], 'findings': [], 'techniques': [], 'problems': []}
    for e in g.inn.get(node_id, []):
        s = e['s']; t = s.split(':', 1)[0]
        if e['p'] in ('targets_game', 'approach', 'source_platform', 'target_platform', 'uses_engine', 'donor_engine', 'uses_tool', 'uses_tech', 'built_with') and t == 'project': c['projects'].append(s)
        elif e['p'] == 'about' and t == 'exp': c['experiments'].append(s)
        elif e['p'] == 'about' and t == 'finding': c['findings'].append(s)
        elif e['p'] == 'applies_to' and t == 'technique': c['techniques'].append(s)
        elif e['p'] == 'affects' and t == 'problem': c['problems'].append(s)
    for e in g.out.get(node_id, []):
        if e['p'] == 'problem': c['problems'].append(e['o'])
    return c


def prior_art_entities(query, limit=3):
    """Graph entities named in a query, in card order (games, projects, engines, approaches, subsystems...)."""
    g = graph()
    if not g: return []
    matched = []
    for alias, ids in g.match_text(query):
        for i in ids:
            if i.split(':', 1)[0] not in ('exp', 'finding') and i not in matched: matched.append(i)
    order = {'game': 0, 'project': 1, 'engine': 2, 'approach': 3, 'subsystem': 4, 'tech': 5, 'technique': 6, 'problem': 7}
    matched.sort(key=lambda i: order.get(i.split(':', 1)[0], 9))
    return matched[:limit]


def tried(query, project=None, limit=4):
    """Experiments similar to an idea, best first; weak neighbours of the best match are dropped."""
    docs = docs_for({'experiments'})
    if project: docs = [d for d in docs if d.extra['project'] == project]
    hits = rank(docs, query, limit * 3, extra=expansion(query), min_frac=0.34)
    if hits: hits = [h for h in hits if h[0] >= 0.4 * hits[0][0]][:limit]
    return hits

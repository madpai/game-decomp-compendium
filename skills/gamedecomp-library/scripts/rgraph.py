"""Research graph: a small, auditable set of typed relationships between games, engines, technology, techniques,
projects, formats, problems, findings and experiments.

Source of truth (hand-written, one record per line, diff-friendly): knowledge/graph/{nodes,edges,findings}.jsonl and
knowledge/experiments/*.md. `refresh/build_knowledge.py` validates them and writes the generated data/graph.json that
this module loads (so an installed skill needs no repository). Nothing here is a database: lookups are dictionaries and
breadth-first searches over a few hundred edges.

An edge is [subject, predicate, object, level, source, note]. `level` says how well that one edge is supported, `source`
points to where (see POINTERS), and a missing edge means *unknown*, never *no*.
"""
import collections, json, os, re

LEVELS = ['guessed', 'inferred', 'documented', 'static', 'verified']
LEVEL_HELP = {
    'guessed': 'plausible, unchecked; a hypothesis to test',
    'inferred': 'our own reasoning from evidence we hold; the step from evidence to claim is not measured',
    'documented': 'stated by an upstream source we read (spec, wiki, README, project docs) but did not check ourselves',
    'static': 'read directly from a binary, source tree or data file (no running, no independent oracle)',
    'verified': 'measured or observed with an oracle; independent confirmation is recorded separately',
}
SCOPES = ['build', 'project', 'family']
SCOPE_HELP = {
    'build': 'a fact about specific game build(s), slice or data set named in the record',
    'project': 'one project\'s implementation choice, or an upstream pin; never an engine fact',
    'family': 'holds across several builds/games; needs independent confirmation recorded',
}
NODE_TYPES = ['game', 'engine', 'tech', 'compiler', 'platform', 'fmt', 'struct', 'subsystem', 'technique', 'approach',
              'project', 'problem', 'finding', 'exp']
RESULTS = ['worked', 'failed', 'partial', 'inconclusive']

ANY = set(NODE_TYPES)
# predicate -> (allowed subject types, allowed object types, meaning)
PREDICATES = {
    'uses_engine': ({'game', 'project'}, {'engine'}, 'built on / runs on this engine'),
    'uses_physics': ({'game', 'engine'}, {'tech'}, 'physics middleware or library used'),
    'uses_tech': ({'game', 'engine', 'project'}, {'tech'}, 'other middleware or library used'),
    'built_with': ({'game', 'project'}, {'compiler'}, 'compiler / toolchain that produced the shipped binary or the project'),
    'archive_format': ({'game'}, {'fmt'}, 'container format of the shipped data'),
    'asset_format': ({'game'}, {'fmt'}, 'model / texture / animation format of the shipped assets'),
    'data_format': ({'game'}, {'fmt'}, 'plugin / record / script data format'),
    'source_platform': ({'game', 'project'}, {'platform'}, 'platform the original game or input binary runs on'),
    'target_platform': ({'project'}, {'platform'}, 'platform the project wants to run on'),
    'targets_game': ({'project', 'engine'}, {'game'}, 'game the project reimplements, ports, mods or studies'),
    'donor_engine': ({'project'}, {'engine'}, 'existing engine the project is built on and patches'),
    'approach': ({'project', 'engine'}, {'approach'}, 'strategy the project follows'),
    'uses_tool': ({'project'}, {'project'}, 'another project used as a tool'),
    'uses_technique': ({'project'}, {'technique'}, 'technique the project applies'),
    'problem': ({'project', 'game'}, {'problem'}, 'known problem area for this project or game'),
    'reverse_engineered': ({'project'}, {'subsystem'}, 'project recovered some original behaviour or data semantics of the subsystem; the note says which part'),
    'applies_to': ({'technique', 'approach'}, ANY, 'where the technique or approach is known (or suspected) to work'),
    'part_of': ({'struct', 'subsystem'}, {'subsystem', 'tech', 'engine', 'fmt'}, 'belongs to'),
    'wraps': ({'struct'}, {'struct'}, 'contains / wraps another structure'),
    'serialized_in': ({'struct'}, {'fmt'}, 'stored as a block of this file format'),
    'affects': ({'problem'}, {'subsystem'}, 'the problem shows up in this subsystem'),
    # derived by the builder from findings and experiments; not written by hand
    'about': ({'finding', 'exp'}, ANY, 'what the finding or experiment is about'),
    'in_project': ({'exp'}, {'project'}, 'project the experiment ran in'),
    'supersedes': ({'exp'}, {'exp'}, 'newer record replacing an older one'),
}
DERIVED = {'about', 'in_project', 'supersedes'}
# edges that describe properties of a thing and may be followed when asking "does X use Y, however indirectly"
HOP = {'targets_game', 'uses_engine', 'uses_physics', 'uses_tech', 'built_with', 'donor_engine', 'archive_format',
       'asset_format', 'data_format', 'source_platform', 'target_platform', 'approach', 'uses_tool'}
POINTERS = ('ref:<skill>/<file>[#heading]', 'note:<path under knowledge/>', 'exp:<ID>', 'catalog:<id>', 'playbook:<id>',
            'repo:<owner>/<name>/<path>', 'url:<https://...>', 'finding:<id>')


def norm(s):
    return ' '.join(re.findall(r'[a-z0-9]+', (s or '').lower().replace('↔', ' ')))


def level_rank(level):
    return LEVELS.index(level) if level in LEVELS else -1


def split_sources(s):
    return [p.strip() for p in (s or '').split(';') if p.strip()]


# ------------------------------------------------------------------ validation (used by build_knowledge.py)
def check_pointer(ptr, ctx):
    """Return an error string, or None when the pointer resolves. ctx: repo_root, exp_ids, catalog_ids, playbook_ids, finding_ids."""
    kind, _, rest = ptr.partition(':')
    root = ctx.get('repo_root')
    if kind == 'ref':
        path, _, heading = rest.partition('#')
        p = os.path.join(root, 'skills', path)
        if not os.path.isfile(p): return f'ref file missing: {path}'
        if heading and norm(heading) not in norm(open(p, encoding='utf-8').read()): return f'heading not found in {path}: {heading}'
    elif kind == 'note':
        if not os.path.isfile(os.path.join(root, 'knowledge', rest)): return f'note missing: {rest}'
    elif kind == 'exp':
        if rest not in ctx['exp_ids']: return f'unknown experiment {rest}'
    elif kind == 'catalog':
        if rest not in ctx['catalog_ids']: return f'unknown catalog id {rest}'
    elif kind == 'playbook':
        if rest not in ctx['playbook_ids']: return f'unknown playbook {rest}'
    elif kind == 'finding':
        if 'finding:' + rest not in ctx['finding_ids']: return f'unknown finding {rest}'
    elif kind == 'repo':
        if rest.count('/') < 2: return f'repo pointer needs owner/name/path: {rest}'
    elif kind == 'url':
        if not rest.startswith('https://'): return f'url pointer must be https: {rest}'
    else:
        return f'unknown pointer kind {kind!r} (use {", ".join(POINTERS)})'
    return None


def node_type(node_id):
    return node_id.split(':', 1)[0]


def validate(nodes, edges, findings, ctx):
    """nodes: list of dicts, edges: list of lists, findings: list of dicts. Returns a list of problem strings."""
    bad = []
    ids = {}
    for n in nodes:
        i = n.get('id', '')
        t = node_type(i)
        if t not in NODE_TYPES or t in ('finding', 'exp'): bad.append(f'node {i!r}: type must be one of {[x for x in NODE_TYPES if x not in ("finding", "exp")]}')
        if i in ids: bad.append(f'duplicate node {i}')
        ids[i] = n
        if not n.get('name'): bad.append(f'node {i}: name missing')
        if not n.get('summary'): bad.append(f'node {i}: summary missing')
        for k in ('aliases', 'cues'):
            if not isinstance(n.get(k, []), list): bad.append(f'node {i}: {k} must be a list')
        if n.get('catalog') and n['catalog'] not in ctx['catalog_ids']: bad.append(f'node {i}: unknown catalog id {n["catalog"]}')
        extra = set(n) - {'id', 'name', 'aliases', 'cues', 'summary', 'url', 'catalog'}
        if extra: bad.append(f'node {i}: unknown keys {sorted(extra)}')
    # aliases must not be ambiguous between nodes (a shared alias would make `graph show X` guess)
    seen = {}
    for n in nodes:
        for a in [n.get('name', '')] + list(n.get('aliases', [])) + [n.get('id', '').split(':', 1)[-1]]:
            k = norm(a)
            if not k: continue
            if k in seen and seen[k] != n['id']: bad.append(f'alias {a!r} is shared by {seen[k]} and {n["id"]}')
            seen.setdefault(k, n['id'])
    allids = set(ids) | {f['id'] for f in findings} | set(ctx.get('exp_node_ids', []))
    seen_edges = set()
    for e in edges:
        if not isinstance(e, list) or len(e) not in (5, 6):
            bad.append(f'edge must be [s,p,o,level,source(,note)]: {e}'); continue
        s, p, o, level, source = e[:5]
        tag = f'edge {s} {p} {o}'
        if p not in PREDICATES: bad.append(f'{tag}: unknown predicate'); continue
        if p in DERIVED: bad.append(f'{tag}: {p} is derived; do not write it by hand'); continue
        if s not in ids: bad.append(f'{tag}: unknown subject'); continue
        if o not in ids: bad.append(f'{tag}: unknown object'); continue
        dom, rng, _ = PREDICATES[p]
        if node_type(s) not in dom: bad.append(f'{tag}: subject type {node_type(s)} not allowed (allowed {sorted(dom)})')
        if node_type(o) not in rng: bad.append(f'{tag}: object type {node_type(o)} not allowed (allowed {sorted(rng)})')
        if level not in LEVELS: bad.append(f'{tag}: level {level!r} not in {LEVELS}')
        if (s, p, o) in seen_edges: bad.append(f'{tag}: duplicate edge')
        seen_edges.add((s, p, o))
        srcs = split_sources(source)
        if not srcs: bad.append(f'{tag}: source missing')
        for ptr in srcs:
            err = check_pointer(ptr, ctx)
            if err: bad.append(f'{tag}: {err}')
        if level == 'guessed' and not (e[5] if len(e) == 6 else ''): bad.append(f'{tag}: a guessed edge needs a note saying how to check it')
    fids = set()
    for f in findings:
        i = f.get('id', '')
        tag = f'finding {i}'
        if not i.startswith('finding:'): bad.append(f'{tag}: id must start with finding:')
        if i in fids: bad.append(f'{tag}: duplicate')
        fids.add(i)
        extra = set(f) - {'id', 'claim', 'level', 'scope', 'build', 'about', 'oracle', 'source', 'unverified', 'confirmed_by', 'note'}
        if extra: bad.append(f'{tag}: unknown keys {sorted(extra)}')
        claim = f.get('claim', '')
        if not claim or len(claim) > 420: bad.append(f'{tag}: claim missing or longer than 420 chars (findings are atomic)')
        if f.get('level') not in LEVELS: bad.append(f'{tag}: bad level')
        if f.get('scope') not in SCOPES: bad.append(f'{tag}: bad scope (use {SCOPES})')
        if f.get('scope') == 'build' and len(f.get('build', '')) < 10: bad.append(f'{tag}: scope build needs a build/version/slice description')
        if f.get('level') in ('static', 'verified') and len(f.get('oracle', '')) < 15: bad.append(f'{tag}: static/verified needs an oracle (what was read or measured, and how it was checked)')
        if len(f.get('unverified', '')) < 10: bad.append(f'{tag}: say what remains unverified')
        if not f.get('about'): bad.append(f'{tag}: about missing')
        for a in f.get('about', []):
            if a not in ids: bad.append(f'{tag}: about unknown node {a}')
        srcs = f.get('source', [])
        if not isinstance(srcs, list) or not srcs: bad.append(f'{tag}: source must be a non-empty list of pointers')
        conf = f.get('confirmed_by', [])
        for ptr in list(srcs) + list(conf):
            err = check_pointer(ptr, {**ctx, 'finding_ids': fids | {x['id'] for x in findings}})
            if err: bad.append(f'{tag}: {err}')
        if f.get('scope') == 'family' and not conf: bad.append(f'{tag}: family scope needs confirmed_by (independent evidence)')
        if f.get('level') == 'verified' and f.get('scope') == 'family' and not conf: bad.append(f'{tag}: verified family claims need confirmed_by')
    return bad


# ------------------------------------------------------------------ the query side
class Graph:
    def __init__(self, data):
        self.nodes = data['nodes']                       # id -> node dict (attrs for finding/exp included)
        self.edges = data['edges']                       # list of dicts {s,p,o,level,source,note}
        self.out = collections.defaultdict(list)
        self.inn = collections.defaultdict(list)
        for e in self.edges:
            self.out[e['s']].append(e)
            self.inn[e['o']].append(e)
        self.alias = collections.defaultdict(set)        # normalised alias -> node ids
        for i, n in self.nodes.items():
            if node_type(i) in ('finding', 'exp'): continue
            for a in [n['name'], i.split(':', 1)[-1]] + list(n.get('aliases', [])):
                k = norm(a)
                if k: self.alias[k].add(i)

    # -- lookup
    def resolve(self, term):
        """Node ids for a user term: exact id, exact alias/name, else whole-word phrase inside an alias."""
        if term in self.nodes: return [term]
        k = norm(term)
        if not k: return []
        if k in self.alias: return sorted(self.alias[k])
        hits = set()
        for a, ids in self.alias.items():
            if f' {k} ' in f' {a} ': hits |= ids
        return sorted(hits)

    def match_text(self, text):
        """Nodes whose alias occurs as a whole phrase in free text (longest alias wins; overlapping shorter ones are dropped)."""
        t = f' {norm(text)} '
        cands = sorted(((len(a), a, ids) for a, ids in self.alias.items() if len(a) > 1 and f' {a} ' in t), reverse=True)
        taken, out = [], []
        for _, a, ids in cands:
            if any(f' {a} ' in f' {b} ' for b in taken): continue
            taken.append(a)
            out.append((a, sorted(ids)))
        return out

    def title(self, i):
        n = self.nodes.get(i)
        return n['name'] if n else i

    # -- traversal
    def reach(self, start, max_depth=3, min_level=None):
        """Forward breadth-first search over HOP predicates. Returns {node: (path of edges, weakest level rank)}."""
        floor = level_rank(min_level) if min_level else -1
        best = {start: ([], len(LEVELS))}
        frontier = [start]
        for _ in range(max_depth):
            nxt = []
            for u in frontier:
                path, weak = best[u]
                for e in self.out.get(u, []):
                    if e['p'] not in HOP: continue
                    r = level_rank(e['level'])
                    if r < floor: continue
                    v = e['o']
                    w = min(weak, r)
                    if v not in best or (len(path) + 1 == len(best[v][0]) and w > best[v][1]):
                        best[v] = (path + [e], w); nxt.append(v)
            frontier = nxt
        return best

    def find(self, ntype, has=(), rel=(), min_level=None):
        """Nodes of a type that reach every `has` term and have every `rel` (PRED:TERM) relation.
        Returns [(node_id, [evidence lines])]. PRED may also be `experiment` or `failed` (experiments in that project about TERM)."""
        results = []
        cands = [i for i in self.nodes if node_type(i) == ntype]
        has_t = [(h, set(self.resolve(h))) for h in has]
        rel_t = []
        for r in rel:
            pred, _, term = r.partition(':')
            rel_t.append((pred, term, set(self.resolve(term))))
        floor = level_rank(min_level) if min_level else -1
        for c in cands:
            ev = []
            ok = True
            reach = self.reach(c, 3, min_level)
            for h, targets in has_t:
                if not targets: ok = False; ev.append(f'? could not resolve {h!r} to a node'); break
                hit = [(t, reach[t]) for t in targets if t in reach]
                if not hit: ok = False; break
                t, (path, weak) = max(hit, key=lambda x: (-len(x[1][0]), x[1][1]))
                via = ' '.join(f"-{e['p']}-> {self.title(e['o'])}" for e in path) or '(itself)'
                ev.append(f'has {h}: {via}' + (f' [weakest edge: {LEVELS[weak]}]' if path else ''))
            if not ok: continue
            for pred, term, targets in rel_t:
                if not targets: ok = False; ev.append(f'? could not resolve {term!r} to a node'); break
                found = []
                if pred in ('experiment', 'failed'):
                    for e in self.inn.get(c, []):
                        if e['p'] != 'in_project': continue
                        x = e['s']; attrs = self.nodes[x]
                        if pred == 'failed' and attrs.get('result') not in ('failed', 'partial'): continue
                        if any(a['o'] in targets for a in self.out.get(x, []) if a['p'] == 'about'):
                            found.append(f"{x.split(':', 1)[1]} ({attrs.get('result')}, {attrs.get('level')}): {attrs['name']}")
                else:
                    for e in self.out.get(c, []):
                        if (pred in ('any', e['p'])) and e['o'] in targets and level_rank(e['level']) >= floor:
                            found.append(f"{e['p']} -> {self.title(e['o'])} ({e['level']}){': ' + e['note'] if e.get('note') else ''}")
                if not found: ok = False; break
                ev.extend(f'rel {pred}:{term}: {f}' for f in found)
            if ok: results.append((c, ev))
        return results

    def path(self, a, b, max_len=6):
        """Shortest undirected path between two nodes as [(node, edge or None)]."""
        A, B = self.resolve(a), self.resolve(b)
        if not A or not B: return None
        starts = set(A); goals = set(B)
        prev = {s: None for s in starts}
        dq = collections.deque((s, 0) for s in starts)
        while dq:
            u, d = dq.popleft()
            if u in goals:
                seq = []
                while u is not None:
                    pe = prev[u]
                    seq.append((u, pe[1] if pe else None, pe[2] if pe else None))
                    u = pe[0] if pe else None
                return seq[::-1]
            if d >= max_len: continue
            for e in self.out.get(u, []):
                if e['p'] in ('about', 'in_project'): continue
                if e['o'] not in prev: prev[e['o']] = (u, e, '->'); dq.append((e['o'], d + 1))
            for e in self.inn.get(u, []):
                if e['p'] in ('about', 'in_project'): continue
                if e['s'] not in prev: prev[e['s']] = (u, e, '<-'); dq.append((e['s'], d + 1))
        return []

    def summary_line(self, i):
        """One line of the most useful outgoing facts about a node (used by prior-art cards)."""
        keys = ['uses_engine', 'uses_physics', 'built_with', 'archive_format', 'asset_format', 'data_format', 'donor_engine', 'targets_game', 'approach', 'target_platform', 'source_platform']
        parts = []
        for p in keys:
            ts = [self.title(e['o']) for e in self.out.get(i, []) if e['p'] == p]
            if ts: parts.append(f"{p.replace('_', ' ')}: {', '.join(ts)}")
        return '; '.join(parts)


def load_graph():
    from common import load
    return Graph(load('graph.json'))

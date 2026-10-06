#!/usr/bin/env python3
"""One search over everything the compendium knows: decomp/tool projects, agent field notes, engine playbooks, and the
how-to references of the sibling skills.

  hub.py search "oblivion script compiler"            ranked hits across all sources
  hub.py search "anti-cheat easyanticheat" --source notes,playbooks
  hub.py prior-art "Halo"                             grouped answer: projects, field notes, playbook, relevant skill sections
  hub.py show project:veradictus--thief3-decomp       one record in full
  hub.py show ref:decomp-matching-workflow/references/experiment-discipline.md
  hub.py sources                                      the data sources, licences, snapshot dates
  hub.py where                                        paths in use (data dir, clones, repo)

Sources: projects (GameDecompLibrary + Game-Decompilations + user-added), notes (universal-modder field notes and
techniques), playbooks (per-engine modding routes), mskills (universal-modder's own skills), refs (sections of the
skills installed next to this one). Add --full-text to also search note bodies when a local universal-modder clone exists.
Output always names where the full text lives, so read only what the hit points to.
"""
import argparse, collections, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, data_path, LOCAL_DATA, CACHE, REPO, CLONES, SKILLS_ROOT

STOP = set('a an and are as at be by for from has have how i in is it of on or that the this to was what when where which with you your do does did can could should would not no if then than into out up use used using get set new game games'.split())
def toks(text):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9_.+#-]*", (text or '').lower().replace('--', ' ')) if t not in STOP and len(t) > 1]

class Doc:
    __slots__ = ('kind', 'id', 'title', 'text', 'weighted', 'where', 'meta', 'tf', 'len')
    def __init__(self, kind, id, title, text, weighted, where, meta=''):
        self.kind, self.id, self.title, self.text, self.where, self.meta = kind, id, title, text, where, meta
        words = toks(weighted) * 3 + toks(text)
        self.tf = collections.Counter(words); self.len = len(words) or 1

def build_docs(sources, full_text):
    docs = []
    if 'projects' in sources:
        for e in load('catalog.json'):
            txt = ' '.join(filter(None, [e['summary'], e['note'], e['type'], e['platform'], ' '.join(e['tools']), ' '.join(e['compilers']), e['language'] or '']))
            meta = f"{e['category']} | {e['platform']} | {('%.0f%%' % e['progress']) if e['progress'] not in (None, '') else '-'} | {e['license'] or '-'} | ai:{e['ai']} | depth:{e['depth']}"
            docs.append(Doc('project', e['id'], e['name'], txt, e['name'] + ' ' + e['id'], e['url'], meta))
    if 'notes' in sources:
        nd = load('field-notes.json', {'notes': []})['notes'] + load('local-notes.json', {'notes': []})['notes']
        for n in nd:
            body = ''
            if full_text:
                p = os.path.join(CLONES, 'universal-modder', 'knowledge', n['path'])
                if n.get('source') == 'local': p = os.path.join(SKILLS_ROOT, '..', 'knowledge', n['path'])
                if os.path.isfile(p): body = open(p, encoding='utf-8').read()
            txt = ' '.join([n.get('summary', ''), ' '.join(n.get('tags') or []), ' '.join(n.get('tools') or []), n.get('engine') or '', n.get('route') or '', n.get('anti_cheat') or '', body])
            docs.append(Doc('note', n['path'], n['title'], txt, f"{n['title']} {n.get('game','')} {' '.join(n.get('games_also') or [])}", n['url'],
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
    return docs

def rank(docs, query, limit):
    q = toks(query)
    if not q: return []
    n = len(docs); avg = sum(d.len for d in docs) / max(n, 1)
    df = collections.Counter(t for d in docs for t in set(d.tf))
    res = []
    need = max(1, math.ceil(len(set(q)) * 0.5))      # a hit must cover at least half of the distinct query terms
    for d in docs:
        score = 0.0; matched = set()
        for t in q:
            f = d.tf.get(t, 0)
            if not f:
                # light prefix matching helps with plurals / hyphenation ("decompil" in "decompilation")
                f = sum(c for w, c in d.tf.items() if len(t) > 3 and (w.startswith(t) or t.startswith(w) and len(w) > 4)) * 0.5
                if not f: continue
            matched.add(t)
            idf = math.log(1 + (n - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5))
            score += idf * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * d.len / avg))
        if score > 0 and len(matched) >= need: res.append((score, d))
    res.sort(key=lambda x: -x[0])
    return res[:limit]

def snippet(d, q, width=220):
    t = re.sub(r'\s+', ' ', d.text)
    for w in toks(q):
        i = t.lower().find(w)
        if i >= 0:
            s = max(0, i - 60); return ('…' if s else '') + t[s:s + width] + ('…' if s + width < len(t) else '')
    return t[:width]

def show(d, q):
    print(f"[{d.kind}] {d.title}\n    {d.meta}\n    {snippet(d, q)}\n    -> {d.where}")

def cmd_search(a):
    srcs = set((a.source or 'projects,notes,playbooks,mskills,refs').split(','))
    if 'all' in srcs: srcs = {'projects', 'notes', 'playbooks', 'mskills', 'refs'}
    docs = build_docs(srcs, a.full_text)
    hits = rank(docs, a.query, a.limit)
    for s, d in hits: show(d, a.query); print()
    print(f"# {len(hits)} hit(s) over {len(docs)} documents", file=sys.stderr)

def cmd_prior_art(a):
    docs = build_docs({'projects', 'notes', 'playbooks', 'mskills', 'refs'}, a.full_text)
    groups = collections.OrderedDict([('project', 'Decompilation / tool projects'), ('note', 'Agent field notes (what others learned doing it)'), ('playbook', 'Engine playbooks'), ('ref', 'Sections of the installed skills (methods, formats, engine facts)')])
    allhits = rank(docs, a.query, 400)
    print(f"Prior art for: {a.query}\n")
    for kind, label in groups.items():
        hs = [(s, d) for s, d in allhits if d.kind == kind][:a.per_group]
        print(f"== {label}" + ('' if hs else '  (nothing found)'))
        for s, d in hs: show(d, a.query)
        print()
    print("Next: read the top hit of each group before searching the web; if nothing is found, say so and start with game-recon steps (engine, build, anti-cheat, loaders).")

def cmd_show(a):
    kind, _, ident = a.target.partition(':')
    if kind == 'project':
        for e in load('catalog.json'):
            if e['id'] == ident or ident in e['id']:
                print(json.dumps(e, indent=1, ensure_ascii=False)); return
    elif kind in ('note', 'playbook'):
        key = 'notes' if kind == 'note' else 'playbooks'
        pool = (load('field-notes.json')['notes'] + load('local-notes.json', {'notes': []})['notes']) if kind == 'note' else load('playbooks.json')['playbooks']
        for e in pool:
            if ident in (e.get('path'), e.get('id')) or ident in e['path']:
                print(json.dumps(e, indent=1, ensure_ascii=False))
                lp = os.path.join(CLONES, 'universal-modder', 'knowledge' if kind == 'note' else '', e['path'] if kind == 'playbook' else e['path'])
                print(f"\nfull text: {e['url']}" + (f"\nlocal: {lp}" if os.path.isfile(lp) else ''))
                return
    elif kind == 'ref':
        p = os.path.join(SKILLS_ROOT, ident)
        if os.path.isfile(p): print(open(p, encoding='utf-8').read()); return
    sys.exit(f'not found: {a.target}')

def cmd_sources(a):
    for s in load('sources.json')['sources']:
        print(f"{s['id']:<22} {s['kind']:<12} {s['license']:<14} {s['snapshot']:<11} {s['url']}\n    {s['use']}")

def cmd_where(a):
    print('local data :', LOCAL_DATA, '(exists)' if os.path.isdir(LOCAL_DATA) else '(missing)')
    print('cache      :', CACHE); print('clones     :', CLONES); print('skills root:', SKILLS_ROOT); print('repo       :', f'https://github.com/{REPO}')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('search'); p.add_argument('query'); p.add_argument('--source'); p.add_argument('--limit', type=int, default=10); p.add_argument('--full-text', action='store_true'); p.set_defaults(fn=cmd_search)
    p = sub.add_parser('prior-art'); p.add_argument('query'); p.add_argument('--per-group', type=int, default=5); p.add_argument('--full-text', action='store_true'); p.set_defaults(fn=cmd_prior_art)
    p = sub.add_parser('show'); p.add_argument('target'); p.set_defaults(fn=cmd_show)
    sub.add_parser('sources').set_defaults(fn=cmd_sources); sub.add_parser('where').set_defaults(fn=cmd_where)
    a = ap.parse_args(); a.fn(a)

if __name__ == '__main__': main()

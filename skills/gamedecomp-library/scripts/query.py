#!/usr/bin/env python3
"""Query the GameDecompLibrary catalog snapshot shipped with this skill (304 projects) without loading it into context.

examples
  query.py --text "bethesda|gamebryo|oblivion"          # regex over name/summary/note/topics
  query.py --platform "Windows" --compiler MSVC          # x86 PC decomps built with MSVC
  query.py --tool objdiff --min-progress 50              # mature projects using objdiff
  query.py --use game-hooking-patterns                   # entries annotated for a skill
  query.py --category tool --depth deep                  # tools that were read in depth
  query.py --ai ai-ok                                    # projects that welcome or use AI assistance
  query.py --id vswarte--fromsoftware-rs --full          # everything known about one entry (+ local clone path)
  query.py --stats                                       # counts by platform / category / licence / ai policy
  query.py --text isle --json                            # machine-readable

Fields: depth = how deeply the entry was read when the snapshot was made (deep: source/docs; readme; meta: catalog data only).
ai    = the project's stated stance on AI-assisted contribution (human-only | no-ai-decomp | disclose | ai-ok | unspecified).
        Always re-read the project's CONTRIBUTING before sending anything upstream; never open issues/PRs on the user's behalf unasked.
"""
import argparse, collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load as _load
CLONES = os.environ.get('GAMEDECOMP_CLONES', os.path.expanduser('~/.claude/knowledge-cache/gamedecomp/clones'))

def load():
    return _load('catalog.json')

def local_clone(e):
    name = e['url'].rstrip('/').split('/')[-1]
    for cand in (name, name.lower()):
        p = os.path.join(CLONES, cand)
        if os.path.isdir(p): return p
    return None

def line(e):
    prog = '' if e['progress'] in (None, '') else f" {e['progress']:.0f}%"
    ai = '' if e['ai'] == 'unspecified' else f" ai={e['ai']}"
    use = f" -> {','.join(e['use'])}" if e['use'] else ''
    txt = (e['note'] or e['summary'])[:150]
    return f"{e['id']:<46} {e['category']:<6} {(e['platform'] or '')[:14]:<14}{prog:>5} {e['license'] or '-':<12}{ai}{use}\n    {txt}"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--text'); ap.add_argument('--id'); ap.add_argument('--platform'); ap.add_argument('--category')
    ap.add_argument('--compiler'); ap.add_argument('--tool'); ap.add_argument('--use'); ap.add_argument('--license'); ap.add_argument('--lang')
    ap.add_argument('--ai'); ap.add_argument('--depth'); ap.add_argument('--min-progress', type=float); ap.add_argument('--sort', default='stars', choices=['stars', 'progress', 'pushed', 'id'])
    ap.add_argument('--limit', type=int, default=40); ap.add_argument('--full', action='store_true'); ap.add_argument('--json', action='store_true'); ap.add_argument('--stats', action='store_true')
    a = ap.parse_args()
    rows = load()
    if a.stats:
        for key in ('category', 'license', 'ai', 'depth'):
            print(key, dict(collections.Counter(str(r[key]) for r in rows).most_common()))
        print('platform', dict(collections.Counter(re.sub(r' \(derived\)| [0-9][0-9.]*.*$', '', (r['platform'] or '?')) for r in rows).most_common(18)))
        return
    def ok(e):
        if a.id and e['id'] != a.id and a.id not in e['id']: return False
        if a.category and e['category'] != a.category: return False
        if a.platform and not re.search(a.platform, e['platform'] or '', re.I): return False
        if a.compiler and not any(re.search(a.compiler, c, re.I) for c in e['compilers']): return False
        if a.tool and not any(re.search(a.tool, t, re.I) for t in e['tools']): return False
        if a.use and a.use not in e['use']: return False
        if a.license and not re.search(a.license, e['license'] or '', re.I): return False
        if a.lang and not re.search(a.lang, e['language'] or '', re.I): return False
        if a.ai and e['ai'] != a.ai: return False
        if a.depth and e['depth'] != a.depth: return False
        if a.min_progress is not None and (e['progress'] or 0) < a.min_progress: return False
        if a.text:
            hay = ' '.join([e['id'], e['name'], e['summary'], e['note'], e['type'] or '', e['group'] or ''])
            if not re.search(a.text, hay, re.I): return False
        return True
    res = [e for e in rows if ok(e)]
    keyf = {'stars': lambda e: -(e['stars'] or 0), 'progress': lambda e: -(e['progress'] or 0), 'pushed': lambda e: e['pushed'] or '', 'id': lambda e: e['id']}[a.sort]
    res.sort(key=keyf)
    if a.json:
        print(json.dumps(res[:a.limit], indent=1, ensure_ascii=False)); return
    for e in res[:a.limit]:
        print(line(e))
        if a.full:
            for k in ('name', 'url', 'type', 'group', 'language', 'stars', 'pushed', 'archived', 'compilers', 'tools', 'build', 'summary', 'note', 'depth', 'ai'):
                print(f"      {k}: {e[k]}")
            lc = local_clone(e)
            print(f"      local clone: {lc or 'none (see scripts/clone.sh to fetch)'}")
    print(f"# {len(res)} match(es){' (showing %d)' % a.limit if len(res) > a.limit else ''}", file=sys.stderr)

if __name__ == '__main__': main()

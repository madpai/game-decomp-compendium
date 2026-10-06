#!/usr/bin/env python3
"""Index this repository's own field notes (knowledge/**/*.md) into data/local-notes.json and knowledge/INDEX.md.

usage: index_local_notes.py [--repo-root DIR] [--check]
Front matter is a simple `key: value` block (lists as JSON or [a, b, c]); the same keys as universal-modder's template,
so a note can be offered upstream unchanged (only with the user's approval). Notes are validated: required keys, a Gotchas
section, no fenced code block over 150 lines, no obvious secrets or private paths. Each numbered gotcha is also stored as
{n, symptom, cause, fix} so `hub.py diagnose` can search problems directly.
`--check` writes nothing and fails when the generated files are out of date. Exit code 1 on a validation failure.
Normally run through build_knowledge.py (notes + experiments + graph in one go)."""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ('kind', 'title', 'status', 'agents', 'date')
BASE = 'https://github.com/madpai/game-decomp-compendium/blob/main/knowledge/'
SKIP = ('README.md', 'INDEX.md', 'TEMPLATE.md')
PRIVATE = re.compile(r'(/home/[a-z0-9_.-]+|/mnt/media|openoblivion-private|ghp_[A-Za-z0-9]|gho_[A-Za-z0-9]|AKIA[0-9A-Z]{12}|api[_-]?key\s*[:=]\s*\S{12,})', re.I)
HEX = re.compile(r'0x[0-9a-fA-F]{6,}')
HEX_OK = re.compile(r'timestamp|build|formid|hash|sha|checksum|crc|magic|image base|mask|modulo|% 0x', re.I)


def parse(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not m: return None, text
    fm = {}
    for line in m.group(1).splitlines():
        if not line or line.startswith((' ', '#', '-')): continue
        k, _, v = line.partition(':'); v = v.strip()
        if v[:1] in '[{"':
            try: v = json.loads(v)
            except ValueError:
                if v[:1] == '[' and v[-1:] == ']': v = [x.strip().strip('"\'') for x in v[1:-1].split(',') if x.strip()]
                else: v = v.strip('"')
        elif v[:1] == "'": v = v.strip("'")
        fm[k.strip()] = v
    return fm, text[m.end():]


def sections(body):
    """{heading: text} for '## ' sections."""
    parts = re.split(r'(?m)^## (.+)$', body)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def clip(s, n):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def gotcha_items(section):
    """Split a numbered Gotchas section into {n, symptom, cause, fix}. Handles `1. **Symptom.** **Cause:** x **Fix:** y`
    and the nested-bullet style of universal-modder."""
    items = []
    for m in re.finditer(r'(?ms)^(\d+)\.\s+(.*?)(?=^\d+\.\s|\Z)', section):
        raw = re.sub(r'\s*\n\s*(?:-\s+)?', ' ', m.group(2)).strip()
        cause = re.search(r'\*\*Cause:?\*\*:?\s*(.*?)(?=\s\*\*(?:Fix|Diagnose|Workaround|Mitigation|Fix/mitigation)[^*]*\*\*|$)', raw)
        fix = re.search(r'\*\*(?:Fix|Fix/mitigation|Workaround|Mitigation):?\*\*:?\s*(.*?)(?=\s\*\*(?:Diagnose)[^*]*\*\*|$)', raw)
        head = re.match(r'\*\*(.+?)\*\*', raw)
        symptom = head.group(1) if head and not head.group(1).lower().startswith(('cause', 'fix')) else re.split(r'\s\*\*', raw)[0]
        rest = raw[len(head.group(0)):] if head else raw[len(symptom):]
        items.append({'n': int(m.group(1)), 'symptom': clip(symptom.strip('.* '), 220), 'cause': clip(cause.group(1), 420) if cause else '',
                      'fix': clip(fix.group(1), 320) if fix else '', 'detail': '' if cause else clip(rest.replace('**', ''), 300)})
    return items


def lint(rel, text):
    bad = []
    if PRIVATE.search(text): bad.append(f'{rel}: private path or possible secret: {PRIVATE.search(text).group(0)[:40]}')
    for i, line in enumerate(text.splitlines(), 1):
        for h in HEX.findall(line):
            if not HEX_OK.search(line): bad.append(f'{rel}:{i}: hex literal {h} without a build/timestamp/hash/FormID word on the line (no address dumps in a public repo)')
    return bad


def collect(repo_root):
    kd = os.path.join(repo_root, 'knowledge'); notes = []; bad = []
    for dp, dirs, fs in os.walk(kd):
        dirs[:] = [d for d in dirs if d not in ('experiments', 'graph')]
        for f in sorted(fs):
            if not f.endswith('.md') or f in SKIP: continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, kd)
            text = open(p, encoding='utf-8').read(); fm, body = parse(text)
            if fm is None: bad.append(f'{rel}: no front matter'); continue
            for k in REQUIRED:
                if k not in fm: bad.append(f'{rel}: missing {k}')
            if '## Gotchas' not in body: bad.append(f'{rel}: no Gotchas section')
            for blk in re.findall(r'```.*?\n(.*?)```', body, re.S):
                if blk.count('\n') > 150: bad.append(f'{rel}: code block over 150 lines')
            bad += lint(rel, text)
            summ = re.search(r'^>\s*(.+(?:\n>.*)*)', body, re.M)
            sec = sections(body)
            items = gotcha_items(sec.get('Gotchas', ''))
            verif = sec.get('Verification', '')
            notes.append({'path': rel, 'kind': fm.get('kind'), 'title': fm.get('title'), 'game': fm.get('game', ''), 'games_also': fm.get('games_also', []),
                          'game_version': fm.get('game_version', ''), 'platform': fm.get('platform'), 'engine': fm.get('engine'), 'route': fm.get('route'),
                          'tools': fm.get('tools', []), 'anti_cheat': fm.get('anti_cheat', ''), 'status': fm.get('status'), 'agents': fm.get('agents', []),
                          'date': fm.get('date'), 'tags': fm.get('tags', []) if isinstance(fm.get('tags'), list) else [],
                          'url': BASE + rel, 'summary': re.sub(r'\s*\n>\s*', ' ', summ.group(1)).strip()[:500] if summ else '',
                          'verification': clip(verif, 600), 'gotchas': len(items), 'gotcha_items': items, 'source': 'local'})
    notes.sort(key=lambda n: (n['kind'], n['path']))
    return notes, bad


def render(notes):
    lines = ['# Field notes index', '', '_Generated by `skills/gamedecomp-library/scripts/refresh/build_knowledge.py`; do not edit by hand._', '', '| Kind | Note | Engine | Route | Status | Gotchas | Date |', '|---|---|---|---|---|---|---|']
    for n in notes: lines.append(f"| {n['kind']} | [{n['title']}]({n['path']}) | {n.get('engine') or ''} | {n.get('route') or ''} | {n['status']} | {n['gotchas']} | {n['date']} |")
    return {'data': json.dumps({'meta': {'source': 'https://github.com/madpai/game-decomp-compendium', 'license': 'MIT'}, 'notes': notes}, indent=0, ensure_ascii=False),
            'index': '\n'.join(lines) + '\n'}


def targets(repo_root):
    return {'data': os.path.join(repo_root, 'skills', 'gamedecomp-library', 'data', 'local-notes.json'), 'index': os.path.join(repo_root, 'knowledge', 'INDEX.md')}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo-root', default=os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    notes, bad = collect(a.repo_root)
    out, tg = render(notes), targets(a.repo_root)
    if a.check:
        for k, p in tg.items():
            if not os.path.isfile(p) or open(p, encoding='utf-8').read() != out[k]: bad.append(f'{os.path.relpath(p, a.repo_root)} is out of date: run refresh/build_knowledge.py')
    else:
        for k, p in tg.items(): open(p, 'w', encoding='utf-8').write(out[k])
    print(f'{len(notes)} notes indexed', ('; PROBLEMS:\n  ' + '\n  '.join(bad)) if bad else '')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()

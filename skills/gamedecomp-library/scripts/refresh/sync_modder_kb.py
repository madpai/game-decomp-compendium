#!/usr/bin/env python3
"""Snapshot the rehan-remade/universal-modder knowledge base (MIT) into this skill's data/ folder.

usage: sync_modder_kb.py [--clone-dir DIR] [--pull] [--out DATA_DIR]

Reads (from a shallow clone, created if missing):
  knowledge/index.json                           -> data/field-notes.json   (agent-written field notes + techniques)
  skills/mod-any-game/references/engines/*.md    -> data/playbooks.json     (per-engine modding routes)
  skills/*/SKILL.md                              -> data/modder-skills.json (the repo's own agent skills, name + description)
Only metadata and short extracts are stored; full note text stays upstream (the clone, or the `url` of each record).
"""
import argparse, json, os, re, subprocess, sys
REPO = 'https://github.com/rehan-remade/universal-modder'
RAW = 'https://github.com/rehan-remade/universal-modder/blob/main/'
HERE = os.path.dirname(os.path.abspath(__file__))

def frontmatter(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(':')
            if k and not line.startswith(' '): out[k.strip()] = v.strip().strip('"')
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clone-dir', default=os.path.expanduser('~/.claude/knowledge-cache/gamedecomp/clones/universal-modder'))
    ap.add_argument('--pull', action='store_true'); ap.add_argument('--out', default=os.path.join(HERE, '..', '..', 'data'))
    a = ap.parse_args()
    if not os.path.isdir(a.clone_dir):
        os.makedirs(os.path.dirname(a.clone_dir), exist_ok=True)
        subprocess.run(['git', 'clone', '-q', '--depth', '1', REPO + '.git', a.clone_dir], check=True)
    elif a.pull:
        subprocess.run(['git', '-C', a.clone_dir, 'pull', '-q', '--ff-only'], check=False)
    rev = subprocess.run(['git', '-C', a.clone_dir, 'log', '-1', '--format=%H %cs'], capture_output=True, text=True).stdout.strip()
    kb = json.load(open(os.path.join(a.clone_dir, 'knowledge', 'index.json')))
    notes = []
    for n in kb:
        path = n['path']
        n['url'] = RAW + 'knowledge/' + path
        # pull the gotcha count + first sentence of the blockquote summary as a cheap retrieval aid
        try:
            body = open(os.path.join(a.clone_dir, 'knowledge', path), encoding='utf-8').read()
            summ = re.search(r'^>\s*(.+(?:\n>.*)*)', body, re.M)
            n['summary'] = re.sub(r'\s*\n>\s*', ' ', summ.group(1)).strip()[:500] if summ else ''
            g = re.search(r'## Gotchas\n(.*?)(?:\n## |\Z)', body, re.S)
            n['gotchas'] = len(re.findall(r'^\d+\.\s', g.group(1), re.M)) if g else 0
        except OSError:
            n['summary'], n['gotchas'] = '', 0
        notes.append(n)
    play = []
    pdir = os.path.join(a.clone_dir, 'skills', 'mod-any-game', 'references', 'engines')
    for f in sorted(os.listdir(pdir)):
        t = open(os.path.join(pdir, f), encoding='utf-8').read()
        title = re.search(r'^# (.+)', t, re.M)
        ident = re.search(r'\*\*Identify\.\*\*\s*(.+)', t)
        play.append({'id': f[:-3], 'title': title.group(1) if title else f, 'identify': ident.group(1)[:300] if ident else '',
                     'headings': re.findall(r'^##+ (.+)', t, re.M)[:20], 'bytes': len(t),
                     'url': RAW + 'skills/mod-any-game/references/engines/' + f, 'path': 'skills/mod-any-game/references/engines/' + f})
    skills = []
    sdir = os.path.join(a.clone_dir, 'skills')
    for d in sorted(os.listdir(sdir)):
        p = os.path.join(sdir, d, 'SKILL.md')
        if os.path.isfile(p):
            fm = frontmatter(open(p, encoding='utf-8').read())
            skills.append({'name': fm.get('name', d), 'description': fm.get('description', '')[:400], 'url': RAW + f'skills/{d}/SKILL.md'})
    os.makedirs(a.out, exist_ok=True)
    meta = {'source': REPO, 'license': 'MIT', 'revision': rev}
    json.dump({'meta': meta, 'notes': notes}, open(os.path.join(a.out, 'field-notes.json'), 'w'), indent=0, ensure_ascii=False)
    json.dump({'meta': meta, 'playbooks': play}, open(os.path.join(a.out, 'playbooks.json'), 'w'), indent=0, ensure_ascii=False)
    json.dump({'meta': meta, 'skills': skills}, open(os.path.join(a.out, 'modder-skills.json'), 'w'), indent=0, ensure_ascii=False)
    print(f'{len(notes)} notes, {len(play)} playbooks, {len(skills)} skills from {rev}')

if __name__ == '__main__': main()

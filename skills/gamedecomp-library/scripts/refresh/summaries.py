#!/usr/bin/env python3
"""Derive a short factual summary + compiler/toolchain hints for each catalog entry from its harvested README."""
import json, re, html
from pathlib import Path
root = Path(__file__).resolve().parent.parent
index = json.load(open(root/'index.json'))

COMPILERS = [
 ('MWCC (Metrowerks CodeWarrior)', r'\bmwcc\b|metrowerks|codewarrior|mwcceppc|mwldeppc'),
 ('MSVC (Visual C++)', r'\bMSVC\b|Visual C\+\+|cl\.exe|Visual Studio|\bVC6\b|\bVC7\b|msvc ?[0-9]'),
 ('IDO (SGI)', r'\bIDO\b'),
 ('GCC / GNU', r'\bgcc\b|\bg\+\+\b|arm-none-eabi|agbcc|mips-linux-gnu|psyq|\bsn ?systems\b|ee-gcc'),
 ('Clang / LLVM', r'\bclang\b|\bllvm\b'),
 ('Watcom', r'watcom'),
 ('CodeWarrior/SN/other', r'\bsn compiler\b|\bsnc\b|\bProDG\b|devkitpro|devkitppc'),
]
def clean(md):
    md = re.sub(r'<!--.*?-->', '', md, flags=re.S)
    md = re.sub(r'<(script|style).*?</\1>', '', md, flags=re.S|re.I)
    md = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md)
    md = re.sub(r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)', '', md)
    md = re.sub(r'^\[[^\]]+\]:\s*\S+.*$', '', md, flags=re.M)
    md = re.sub(r'<[^>]+>', ' ', md)
    md = html.unescape(md)
    md = re.sub(r'\[!\[[^\]]*\]\[[^\]]*\]\]\[[^\]]*\]', '', md)
    md = re.sub(r'!\[[^\]]*\]\[[^\]]*\]', '', md)
    md = re.sub(r'\[\]\([^)]*\)', '', md)
    md = re.sub(r'\[([^\]]+)\]\[[^\]]*\]', r'\1', md)
    md = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', md)
    md = re.sub(r'^\s*[=\-]{3,}\s*$', '', md, flags=re.M)
    md = re.sub(r'[*_`]{1,3}', '', md)
    return md
def first_sentence(md):
    md = clean(md)
    best = ''
    for para in re.split(r'\n\s*\n', md):
        p = ' '.join(l.strip() for l in para.splitlines()).strip()
        if not p or p.startswith('#') or p.startswith('|') or p.startswith('---') or p.startswith('=') or p.startswith('>'): 
            # headings carry little; skip
            if p.startswith('>') and len(p) > 40: pass
            else: continue
        if len(p) < 35: continue
        if re.match(r'^(table of contents|contents|license|building|install|usage|discord|join)', p, re.I): continue
        if re.search(r'(shields\.io|badge|build status|progress:)', p, re.I) and len(p) < 120: continue
        m = re.match(r'(.{30,260}?[.!?])(\s|$)', p)
        best = (m.group(1) if m else p[:240]).strip()
        break
    return best
PLAT = [('PlayStation 2', r'\bps2\b|playstation 2|playstation2'), ('PlayStation Portable', r'\bpsp\b'), ('PlayStation', r'\bps1\b|\bpsx\b|playstation(?! 2)'), ('GameCube', r'game ?cube|\bgc\b|\.dol\b'), ('Wii', r'\bwii\b'),
        ('Nintendo 64', r'\bn64\b|nintendo 64'), ('Nintendo DS', r'\bnds\b|nintendo ds'), ('Nintendo 3DS', r'\b3ds\b'), ('Game Boy Advance', r'\bgba\b|game boy advance'), ('Game Boy', r'game ?boy(?! advance)|\bgbc?\b'),
        ('Switch', r'nintendo switch|\bswitch\b'), ('Xbox 360', r'xbox ?360'), ('Xbox', r'\bxbox\b'), ('Dreamcast', r'dreamcast'), ('Saturn', r'\bsaturn\b'), ('SNES', r'\bsnes\b|super nintendo'), ('NES', r'\bnes\b'),
        ('DOS', r'\bdos\b|ms-dos'), ('Windows', r'windows|win32|\.exe\b|directx|msvc|visual c\+\+'), ('Mobile (Android/iOS/J2ME)', r'android|\bios\b|j2me|java me')]
KIND = [('Static recompilation', r'static recomp|\brecomp\b|recompilation'), ('Matching decompilation', r'matching decomp|byte[- ]match|bit[- ]for[- ]bit|\bmatching\b'), ('Disassembly project', r'disassembly'),
        ('Port / reimplementation', r'\bport\b|re-?implementation|re-?creation|reconstruct'), ('Decompilation / reverse engineering', r'decomp|reverse[- ]engineer')]
def guess(rd, table, text_extra=''):
    hay = (rd[:4000] + ' ' + text_extra)
    for label, rx in table:
        if re.search(rx, hay, re.I): return label
    return None
PROHIB = re.compile(r"(?:\b(?:no|not|never|don'?t|do not|without|prohibit\w*|forbid\w*|ban(?:ned)?|reject\w*|refuse\w*|disallow\w*|strictly|zero tolerance)\b[^\n.]{0,90}\b(?:AI|A\.I\.|LLMs?|generative|machine[- ]generated|chat ?gpt|copilot|claude|agents?)\b)|(?:\b(?:AI|LLMs?|generative|machine[- ]generated|chat ?gpt|copilot|claude|agents?)\b[^\n.]{0,90}\b(?:not (?:be )?(?:accepted|allowed|welcome|permitted)|prohibited|forbidden|banned|rejected|will be closed|are not accepted|is not accepted|not tolerated)\b)", re.I)
ALLOW = re.compile(r"\b(?:AI|LLMs?|claude|codex|gpt|agentic|vibe)[- ]?(?:assisted|driven|led|powered|written|generated|developed|coded)\b|developed with (?:the help of )?AI|\bwith (?:the )?(?:help|assistance) of (?:AI|claude|llms?)\b|AI[- ]assisted", re.I)
def ai_policy(rd):
    m = PROHIB.search(rd)
    if m: return 'human-only?', m.group(0)[:160]
    m = ALLOW.search(rd)
    if m: return 'mentions', m.group(0)[:160]
    return 'unspecified', ''
out = []
for r in index:
    raw = root/'raw'/(r['id']+'.json')
    rd = ''
    if raw.exists():
        rd = (json.load(open(raw)).get('readme') or '')
    s = first_sentence(rd) if rd else ''
    s = re.sub(r'\s*\[!\[.*', '', s).strip()
    if len(s) < 35 or s.startswith('[') or s.startswith('+') or s.startswith('-'):
        s = ''
    comps = [n for n, rx in COMPILERS if r['category']=='decomp' and re.search(rx, rd, re.I)]
    r2 = dict(r); r2['summary'] = s; r2['compilers'] = comps
    r2['ai_guess'], r2['ai_evidence'] = ai_policy(rd)
    if not r2.get('platform'):
        r2['platform'] = (guess(rd, PLAT, ' '.join(r.get('topics') or [])) or 'Unknown') + ' (derived)'
        r2['derived'] = True
    if not r2.get('type') or r2.get('type') == 'Game decompilation (list entry)':
        r2['type'] = (guess(rd, KIND, ' '.join(r.get('topics') or [])) or 'Decompilation / reverse engineering') + ' (derived)'
    out.append(r2)
json.dump(out, open(root/'build'/'summaries.json','w'), indent=0)
empty = [r['id'] for r in out if not r['summary']]
print(len(out), 'empty:', len(empty), empty[:40])
import random
random.seed(3)
for r in random.sample(out, 22): print('-', r['id'], '|', r['summary'][:200], '|', r['compilers'])

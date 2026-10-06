#!/usr/bin/env python3
"""Find strings in a PE and the code that references them - the classic "debug string -> function" pivot.

usage: string_xrefs.py FILE --grep REGEX [--wide] [--min-len 4] [--max-xrefs 8] [--json]

Why: game binaries are full of format strings, config keys, script command names and assert text. The code that
loads such a string is almost always the function that implements the feature. This tool lists every matching
string with its VA and every instruction-level reference to it:
  * x86 : any 4-byte absolute operand equal to the string VA (push/mov/cmp/lea imm32/disp32, or a pointer table)
  * x64 : REX + (mov/lea/cmp) with a RIP-relative operand landing on the string
`approx_func` is the first byte after the previous run of int3/nop padding (MSVC pads functions with CC), searched
up to 16 KiB back. It is a hint for where to start reading, not a function boundary you can trust.
Binaries that reference strings through computed tables will need the pointer-table hits (reported as data xrefs).
"""
import argparse, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE

def iter_strings(pe, pattern, wide, minlen):
    rx = re.compile(pattern, re.I)
    for s in pe.sections:
        if not s.readable or s.executable: continue
        blob = bytes(pe.data[s.roff:s.roff + s.rsize])
        if wide:
            for m in re.finditer(rb'(?:[\x20-\x7e]\x00){%d,}' % minlen, blob):
                txt = m.group().decode('utf-16le')
                if rx.search(txt): yield pe.image_base + s.rva + m.start(), txt, s.name
        else:
            for m in re.finditer(rb'[\x20-\x7e\t\r\n]{%d,}' % minlen, blob):
                txt = m.group().decode('latin1')
                if rx.search(txt): yield pe.image_base + s.rva + m.start(), txt, s.name

def approx_function_start(pe, va, back=16384):
    s = pe.section_of_va(va)
    if not s or not s.executable: return None
    base = pe.image_base + s.rva
    lo = max(base, va - back)
    chunk = pe.read_va(lo, va - lo)
    if not chunk: return None
    i = len(chunk) - 1
    while i >= 1:
        if chunk[i - 1] in (0xCC, 0x90, 0xC3, 0xC2) and chunk[i] not in (0xCC, 0x90) and (chunk[i - 1] in (0xCC, 0x90) or True):
            # require padding (CC/90) before: a bare ret is too ambiguous
            if chunk[i - 1] in (0xCC, 0x90): return lo + i
        i -= 1
    return None

def code_xrefs(pe, targets, max_xrefs):
    """targets: dict VA -> label. Returns dict VA -> list of (xref_va, kind)."""
    res = {t: [] for t in targets}
    tset = set(targets)
    for s in pe.sections:
        if not s.readable: continue
        blob = bytes(pe.data[s.roff:s.roff + s.rsize])
        base = pe.image_base + s.rva
        if not pe.is64:
            n = len(blob) - 3
            # fast path: search each target's 4 bytes
            for t in targets:
                pat = struct.pack('<I', t); pos = 0
                while len(res[t]) < max_xrefs:
                    i = blob.find(pat, pos)
                    if i < 0: break
                    res[t].append((base + i, 'code' if s.executable else 'data')); pos = i + 1
        elif s.executable:
            for m in re.finditer(rb'[\x40-\x4f][\x8b\x8d\x89\x3b\x39]([\x05\x0d\x15\x1d\x25\x2d\x35\x3d])', blob, re.S):
                i = m.end()
                if i + 4 > len(blob): continue
                disp = struct.unpack_from('<i', blob, i)[0]
                tgt = base + i + 4 + disp
                if tgt in tset and len(res[tgt]) < max_xrefs: res[tgt].append((base + m.start(), 'rip-rel'))
        else:
            # x64 pointer tables in data
            n = len(blob) // 8
            for k in range(n):
                v = struct.unpack_from('<Q', blob, 8 * k)[0]
                if v in tset and len(res[v]) < max_xrefs: res[v].append((base + 8 * k, 'data'))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--grep', required=True); ap.add_argument('--wide', action='store_true')
    ap.add_argument('--min-len', type=int, default=4); ap.add_argument('--max-xrefs', type=int, default=8); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    pe = PE(a.file)
    found = list(iter_strings(pe, a.grep, a.wide, a.min_len))
    if not found: print('no matching strings', file=sys.stderr); sys.exit(1)
    xr = code_xrefs(pe, {va: t for va, t, _ in found}, a.max_xrefs)
    out = []
    for va, txt, sec in found:
        refs = [{'va': hex(v), 'kind': k, 'approx_func': hex(f) if (f := approx_function_start(pe, v)) else None} for v, k in xr[va]]
        out.append({'va': hex(va), 'section': sec, 'text': txt[:200], 'xrefs': refs})
    if a.json: print(json.dumps(out, indent=1)); return
    for o in out:
        print(f"{o['va']}  [{o['section']}]  {o['text']!r}")
        for r in o['xrefs']: print(f"    <- {r['va']} ({r['kind']})  approx func {r['approx_func']}")
        if not o['xrefs']: print('    (no direct references: look for a pointer table or a computed address)')

if __name__ == '__main__': main()

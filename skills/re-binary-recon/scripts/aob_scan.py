#!/usr/bin/env python3
"""Array-of-bytes signatures: search a PE for a pattern, or build a version-robust signature for a function.

usage:
  aob_scan.py FILE find "48 8B ?? ?? 89 5C"            # all matches (file-wide or --section .text), with RVA/VA
  aob_scan.py FILE make 0x52e320 [--len 48]            # signature for the code at VA, wildcarding operands that move
  aob_scan.py FILE make --rva 0x12345 --len 64
Options: --section NAME, --max N (match limit)

Why signatures instead of addresses: an address is only valid for one build. A signature that wildcards the bytes
that change between builds (absolute pointers, rel32 call/jmp targets, RIP-relative displacements) survives
recompiles and patches. This is the technique used by the "binary mapper" tool in fromsoftware-rs: a TOML profile
of AOBs resolves to RVAs, and a test asserts the resolved RVAs for every supported game build.

`make` is heuristic (no disassembler): it wildcards
  * E8/E9 rel32 operands, 0F 8x rel32 operands (calls/jumps move when code moves),
  * any 4 bytes that read as a pointer into the image (absolute pointers on x86; RVAs through relocations),
  * RIP-relative displacements after REX 8B/8D/89/3B/39 modrm(05|0D|..) on x64,
then reports the SHORTEST PREFIX that is unique in the file. Always re-verify with `find` on every build you care about.
"""
import argparse, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE

def compile_pattern(text):
    toks = text.replace(',', ' ').split()
    pat = bytearray(); mask = []
    for t in toks:
        if t in ('?', '??', '*', '**'): pat.append(0); mask.append(False)
        else: pat.append(int(t, 16)); mask.append(True)
    rx = b''.join(re.escape(bytes([b])) if m else b'.' for b, m in zip(pat, mask))
    return re.compile(rx, re.S), len(pat)

def find_all(pe, text, section=None, limit=50):
    rx, n = compile_pattern(text)
    out = []
    for s in pe.sections:
        if section and s.name != section: continue
        if not section and not s.executable: continue
        blob = bytes(pe.data[s.roff:s.roff + s.rsize])
        for m in rx.finditer(blob):
            out.append((s.rva + m.start(), s.name))
            if len(out) >= limit: return out
    return out

def make_signature(pe, rva, length):
    code = pe.read_rva(rva, length)
    reloc = pe.reloc_rvas() if pe.has_relocs() else set()
    mask = [True] * len(code)
    i = 0
    while i < len(code):
        b = code[i]
        wild = None
        if b in (0xE8, 0xE9) and i + 5 <= len(code): wild = (i + 1, 4)
        elif b == 0x0F and i + 6 <= len(code) and 0x80 <= code[i + 1] <= 0x8F: wild = (i + 2, 4)
        elif pe.is64 and 0x40 <= b <= 0x4F and i + 7 <= len(code) and code[i + 1] in (0x8B, 0x8D, 0x89, 0x3B, 0x39) and (code[i + 2] & 0xC7) == 0x05:
            wild = (i + 3, 4)
        if wild:
            for k in range(wild[0], wild[0] + wild[1]): mask[k] = False
            i = wild[0] + wild[1]; continue
        if not pe.is64 and i + 4 <= len(code):
            v = struct.unpack_from('<I', code, i)[0]
            if pe.in_image(v) and v > pe.image_base + 0x1000 and not any(not mask[k] for k in range(i, i + 4)):
                # only treat as pointer when it points at data/code sections (avoid small immediates)
                for k in range(i, i + 4): mask[k] = False
                i += 4; continue
        if reloc and any((rva + i + k) in reloc for k in range(4)):
            for k in range(i, min(i + 4, len(code))): mask[k] = False
        i += 1
    sig = ' '.join(f'{c:02X}' if m else '??' for c, m in zip(code, mask))
    return sig, code, mask

def shortest_unique(pe, sig, own_rva):
    toks = sig.split()
    for n in range(8, len(toks) + 1):
        pref = ' '.join(toks[:n])
        if pref.endswith('??'): continue
        hits = find_all(pe, pref, limit=2)
        if len(hits) == 1 and hits[0][0] == own_rva: return pref
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('cmd', choices=['find', 'make']); ap.add_argument('arg', nargs='?')
    ap.add_argument('--rva'); ap.add_argument('--len', type=int, default=48); ap.add_argument('--section'); ap.add_argument('--max', type=int, default=50)
    a = ap.parse_args()
    pe = PE(a.file)
    if a.cmd == 'find':
        hits = find_all(pe, a.arg, a.section, a.max)
        for rva, sec in hits: print(f"rva {rva:#x}  va {pe.image_base + rva:#x}  [{sec}]")
        print(f"# {len(hits)} match(es)", file=sys.stderr); sys.exit(0 if hits else 1)
    rva = int(a.rva, 16) if a.rva else int(a.arg, 16) - pe.image_base
    sig, code, mask = make_signature(pe, rva, a.len)
    print('full    :', sig)
    u = shortest_unique(pe, sig, rva)
    print('unique  :', u if u else '(no unique prefix within --len; raise it)')
    print(f"wildcarded {mask.count(False)} of {len(mask)} bytes; rva {rva:#x} va {pe.image_base + rva:#x}")

if __name__ == '__main__': main()

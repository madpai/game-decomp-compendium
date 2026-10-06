#!/usr/bin/env python3
"""Extract the built-in default values of game settings (GMST) from Oblivion.exe's static initializers.

usage: gmst_defaults.py OBLIVION.EXE [--esm Oblivion.esm] [--grep REGEX] [--tsv]

Why: a master file only stores GMST records that differ from the engine's defaults, so settings "absent from the master"
still have values: they are compiled into the executable. Each setting is registered by a static initializer shaped like

    float :  fld dword ptr [DEFAULT]; push ecx; fstp dword ptr [esp]; push offset NAME; mov ecx, offset OBJECT; call Setting::ctor
             (0.0 and 1.0 use fldz / fld1 and put `mov ecx, OBJECT` before `push NAME`)
    int/bool/str:  push IMM (68 imm32 or 6A imm8); push offset NAME; mov ecx, offset OBJECT; call Setting::ctor    (strings: IMM points at the text)

so scanning .text for `68 <NAME> B9 <OBJECT> E8` and looking at the instructions just before gives name -> default. The
name's first letter is the type (f float, i/b int/bool, s string, u unsigned, c char, a/r other).
With --esm the script reads the plugin's GMST records and compares. Expect MOST values to differ: the master overrides the
built-in defaults (placeholders such as "Need a gamesetting description." live in the exe). The oracle for the extraction is
(a) near-complete name coverage of the ESM's GMST records and (b) exact agreement on non-trivial values where the master
happens not to override (e.g. 20, 0.4, 130, 90 across dozens of floats), and (c) an independent objdump-based extractor agreed
on all 711 float defaults it produced (this script also finds fld1/fldz floats, ints and strings).

Output is derived from the executable: keep it private (never commit it); the script itself is generic. Requires the sibling
skill re-binary-recon (pe.py). Validated on the Steam build of Oblivion.exe (x86, MSVC, fixed base).
"""
import argparse, os, re, struct, sys, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 're-binary-recon', 'scripts'))
try:
    from pe import PE
except ImportError:
    sys.exit('needs re-binary-recon/scripts/pe.py next to this skill (install the whole suite)')

NAME_RX = re.compile(rb'^[fibsucar][A-Z][A-Za-z0-9_]{2,60}$')

def decode_value(pe, code, i, kind):
    """Decode the default from the instructions that end at code[i] (the first instruction of the name/object pair)."""
    if kind == 'f':
        seq = code[i - 10:i] if i >= 10 else b''
        if len(seq) == 10 and seq[:2] == b'\xd9\x05' and seq[6:] == b'\x51\xd9\x1c\x24':   # fld [DEFAULT]; push ecx; fstp [esp]
            b = pe.read_va(struct.unpack('<I', seq[2:6])[0], 4)
            return struct.unpack('<f', b)[0] if b else None
        tail = code[i - 6:i] if i >= 6 else b''
        if tail == b'\xd9\xee\x51\xd9\x1c\x24': return 0.0      # fldz
        if tail == b'\xd9\xe8\x51\xd9\x1c\x24': return 1.0      # fld1
        return None
    seq = code[i - 5:i] if i >= 5 else b''
    if len(seq) == 5 and seq[0] == 0x68:                              # push imm32
        imm = struct.unpack('<I', seq[1:])[0]
        if kind == 's':
            sb = pe.read_va(imm, 200) if pe.in_image(imm) else None
            return sb.split(b'\0')[0].decode('latin1') if sb else imm
        return imm - (1 << 32) if (kind == 'i' and imm >= 1 << 31) else imm
    if len(seq) >= 2 and seq[-2] == 0x6A:                             # push imm8 (sign-extended)
        imm = seq[-1] - 256 if seq[-1] >= 128 else seq[-1]
        return imm if kind in 'ib' else imm & 0xFF
    return None

def extract(pe):
    text = next(s for s in pe.sections if s.name == '.text')
    code = bytes(pe.section_bytes(text)); base = pe.image_base + text.rva
    out = {}
    # form A: push NAME ; mov ecx, OBJ ; call      form B: mov ecx, OBJ ; push NAME ; call
    for rx, name_off, start_off in ((rb'\x68(....)\xb9....\xe8....', 1, 0), (rb'\xb9....\x68(....)\xe8....', 6, 0)):
        for m in re.finditer(rx, code, re.S):
            name_va = struct.unpack('<I', m.group(1))[0]
            if not pe.in_image(name_va): continue
            raw = pe.read_va(name_va, 80)
            nm = raw.split(b'\0')[0] if raw else b''
            if not NAME_RX.match(nm): continue
            name = nm.decode('latin1'); kind = name[0]
            val = decode_value(pe, code, m.start(), kind)
            if val is not None: out.setdefault(name, (kind, val, base + m.start()))
    return out

def esm_gmst(path):
    d = open(path, 'rb').read(); res = {}
    def walk(p, end):
        while p < end:
            t = d[p:p + 4]; size = struct.unpack_from('<I', d, p + 4)[0]
            if t == b'GRUP': walk(p + 20, p + size); p += size
            else:
                flags = struct.unpack_from('<I', d, p + 8)[0]
                body = d[p + 20:p + 20 + size]
                if t == b'GMST':
                    if flags & 0x40000: body = zlib.decompress(body[4:])
                    q = 0; edid = None; data = None
                    while q < len(body):
                        st = body[q:q + 4]; sz = struct.unpack_from('<H', body, q + 4)[0]
                        if st == b'EDID': edid = body[q + 6:q + 6 + sz].split(b'\0')[0].decode('latin1')
                        if st == b'DATA': data = body[q + 6:q + 6 + sz]
                        q += 6 + sz
                    if edid and data is not None: res[edid] = data
                p += 20 + size
    walk(0, len(d)); return res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('exe'); ap.add_argument('--esm'); ap.add_argument('--grep'); ap.add_argument('--tsv', action='store_true')
    a = ap.parse_args()
    pe = PE(a.exe); defaults = extract(pe)
    esm = esm_gmst(a.esm) if a.esm else {}
    rows = []
    for name, (kind, val, va) in sorted(defaults.items()):
        if a.grep and not re.search(a.grep, name): continue
        e = esm.get(name); ev = None
        if e is not None:
            if kind == 'f' and len(e) == 4: ev = struct.unpack('<f', e)[0]
            elif kind in 'iubc' and len(e) == 4: ev = struct.unpack('<i', e)[0]
            elif kind == 's': ev = e.split(b'\0')[0].decode('latin1')
        rows.append((name, kind, val, ev))
    for name, kind, val, ev in rows:
        fv = f'{val:.6g}' if isinstance(val, float) else str(val)
        ex = '' if ev is None else (f'{ev:.6g}' if isinstance(ev, float) else str(ev))
        print(f'{name}\t{kind}\t{fv}\t{ex}' if a.tsv else f'{name:<44} {kind}  exe={fv:<14}' + (f' esm={ex}' if ex else ''))
    n = len(rows); both = [(v, ev) for _, k, v, ev in rows if ev is not None]
    agree = sum(1 for v, ev in both if (abs(v - ev) < 1e-5 * max(1, abs(v)) if isinstance(v, float) and isinstance(ev, float) else v == ev))
    print(f'# {n} settings recovered from the exe; {len(both)} also in the ESM; {agree} agree', file=sys.stderr)

if __name__ == '__main__': main()

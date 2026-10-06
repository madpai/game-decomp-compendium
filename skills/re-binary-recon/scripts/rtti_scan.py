#!/usr/bin/env python3
"""Recover C++ class names, vtables and inheritance from MSVC RTTI in a PE file.

usage: rtti_scan.py FILE [--format tsv|json|ghidra|idc] [--min-slots N] [--grep REGEX] [--hierarchy]

How MSVC RTTI is laid out (this is what the scan relies on):
  TypeDescriptor        { void* pVFTable; void* spare; char name[] }   name looks like ".?AVFoo@Bar@@"
  CompleteObjectLocator { sig, offset, cdOffset, pTypeDescriptor, pClassHierarchyDescriptor [, pSelf (x64)] }
  vftable               [ pCompleteObjectLocator ][ slot0 ][ slot1 ] ...   (the COL pointer sits at vftable[-1])
  ClassHierarchyDesc    { sig, attributes, numBaseClasses, pBaseClassArray }
  BaseClassDescriptor   { pTypeDescriptor, numContainedBases, PMD{mdisp,pdisp,vdisp}, attributes, pCHD }
On x86 the pointers are absolute VAs (and the signature is 0); on x64 they are 32-bit RVAs (signature 1).
A class with several vtables (multiple inheritance) has several COLs with different `offset` values.

Output is one row per vtable: class, vtable VA, #slots, COL offset, and the base-class list (MSVC stores the whole
linearised hierarchy, so indirect bases appear too, nearest first; repeated names = repeated sub-objects).
The `ghidra` format emits a script-friendly name list; `idc` emits IDA set-name commands.
Binaries without RTTI (e.g. built with /GR-) simply yield nothing - say so rather than guess.
"""
import argparse, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE

def demangle(raw):
    """'.?AVFoo@Bar@@' -> 'Bar::Foo'.  Templates ('?$') are left readable but not fully expanded."""
    m = re.match(r'\.\?A([VUT])(.*)@@$', raw)
    if not m: return raw
    kind, body = m.groups()
    if '?$' in body:
        return ('struct ' if kind == 'U' else '') + body.replace('@', '::') if False else body
    parts = body.split('@')
    return '::'.join(reversed(parts))

def scan(pe, min_slots=0):
    P = pe.ptr
    data = pe.data
    # 1) type descriptors: find ".?A" strings, descriptor starts 2 pointers earlier
    tds = {}   # VA -> mangled name
    for s in pe.sections:
        if not s.readable: continue
        blob = data[s.roff:s.roff + s.rsize]
        pos = 0
        while True:
            i = blob.find(b'.?A', pos)
            if i < 0: break
            pos = i + 3
            if i < 2 * P or blob[i-1:i] == b'': continue
            j = blob.find(b'\0', i, i + 600)
            if j < 0: continue
            name = blob[i:j]
            if not (name.endswith(b'@@') and re.fullmatch(rb'\.\?A[VUTW][\x20-\x7e]+', name)): continue
            start_rva = s.rva + i - 2 * P
            # pVFTable must be a pointer to type_info's vftable (inside image) or 0
            vt = int.from_bytes(blob[i - 2*P:i - P], 'little')
            if vt and not pe.in_image(vt): continue
            tds[pe.image_base + start_rva] = name.decode('ascii')
    if not tds: return []
    # 2) COLs: dword/rva equal to a type-descriptor at the right field offset
    cols = {}   # COL VA -> dict
    td_by_rva = {va - pe.image_base: n for va, n in tds.items()}
    for s in pe.sections:
        if not s.readable or s.executable: continue
        blob = data[s.roff:s.roff + s.rsize]
        n = len(blob) // 4
        words = struct.unpack_from(f'<{n}I', blob, 0)
        for k in range(3, n - 2):
            w = words[k]
            if pe.is64:
                if w not in td_by_rva: continue
                # fields: sig, offset, cdOffset, pTypeDescriptor(RVA), pClassDescriptor(RVA), pSelf(RVA)
                b = k - 3
                if b < 0 or words[b] != 1: continue
                if b + 5 >= n: continue
                chd_rva = words[b + 4]; self_rva = words[b + 5]
                col_rva = s.rva + b * 4
                if self_rva != col_rva: continue
                cols[pe.image_base + col_rva] = dict(td=pe.image_base + w, chd=pe.image_base + chd_rva, offset=words[b + 1], cd=words[b + 2])
            else:
                if w not in tds: continue
                b = k - 3
                if words[b] != 0: continue
                if b + 4 >= n: continue
                chd = words[b + 4]
                if not pe.in_image(chd): continue
                if words[b + 1] > 0x10000 or words[b + 2] > 0x10000: continue
                cols[pe.image_base + s.rva + b * 4] = dict(td=w, chd=chd, offset=words[b + 1], cd=words[b + 2])
    # 3) vftables: dword equal to a COL VA; the array of code pointers follows it
    rows = []
    col_set = set(cols)
    for s in pe.sections:
        if not s.readable or s.executable: continue
        blob = data[s.roff:s.roff + s.rsize]
        step = P
        for off in range(0, len(blob) - P, step):
            v = int.from_bytes(blob[off:off + P], 'little') if not pe.is64 else int.from_bytes(blob[off:off + 8], 'little')
            if v not in col_set: continue
            slots = 0
            q = off + P
            while q + P <= len(blob):
                p = int.from_bytes(blob[q:q + P], 'little')
                if not (pe.in_image(p) and pe.in_exec(p)): break
                slots += 1; q += P
            vt_va = pe.image_base + s.rva + off + P
            col = cols[v]
            rows.append(dict(vtable=vt_va, slots=slots, col=v, offset=col['offset'], cd_offset=col['cd'], class_td=col['td'], chd=col['chd']))
    # 4) bases from class hierarchy descriptors
    def bases(chd_va):
        raw = pe.read_va(chd_va, 16)
        if not raw or len(raw) < 16: return []
        sig, attr, n, arr = struct.unpack('<IIII', raw)
        if n > 64: return []
        out = []
        for i in range(n):
            if pe.is64:
                r = pe.read_rva(arr + 4 * i, 4)
                if not r: break
                bcd = pe.read_rva(struct.unpack('<I', r)[0], 4)
                if not bcd: break
                tdv = pe.image_base + struct.unpack('<I', bcd)[0]
            else:
                r = pe.u32(arr + 4 * i)
                if r is None: break
                tdv = pe.u32(r)
            if tdv in tds: out.append(demangle(tds[tdv]))
        return out
    result = []
    for r in rows:
        if r['slots'] < min_slots: continue
        td = r['class_td']
        r['class'] = demangle(tds.get(td, '?'))
        r['mangled'] = tds.get(td)
        b = bases(r['chd'])
        r['bases'] = b[1:] if b and b[0] == r['class'] else b   # first entry of the hierarchy is the class itself
        result.append(r)
    result.sort(key=lambda r: r['vtable'])
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--format', default='tsv', choices=['tsv', 'json', 'ghidra', 'idc'])
    ap.add_argument('--min-slots', type=int, default=0); ap.add_argument('--grep'); ap.add_argument('--hierarchy', action='store_true')
    a = ap.parse_args()
    pe = PE(a.file)
    rows = scan(pe, a.min_slots)
    if a.grep: rows = [r for r in rows if re.search(a.grep, r['class'])]
    if not rows:
        print(f"no MSVC RTTI found in {a.file} (built with /GR-, stripped, or not MSVC)", file=sys.stderr); sys.exit(2)
    if a.format == 'json':
        print(json.dumps([{**r, 'vtable': hex(r['vtable']), 'col': hex(r['col']), 'class_td': hex(r['class_td']), 'chd': hex(r['chd'])} for r in rows], indent=1))
    elif a.format == 'ghidra':
        for r in rows: print(f"{r['vtable']:#x}\t{r['class'].replace('::', '__')}__vftable{'' if r['offset'] == 0 else '_%x' % r['offset']}")
    elif a.format == 'idc':
        print('#include <idc.idc>\nstatic main() {')
        for r in rows: print(f"  set_name({r['vtable']:#x}, \"{r['class'].replace('::', '__')}__vftable{'' if r['offset'] == 0 else '_%x' % r['offset']}\", SN_NOWARN);")
        print('}')
    else:
        print('vtable\tslots\tcol_offset\tclass\tbases')
        for r in rows: print(f"{r['vtable']:#x}\t{r['slots']}\t{r['offset']:#x}\t{r['class']}\t{','.join(r['bases'])}")
    print(f"# {len(rows)} vtables, {len({r['class'] for r in rows})} classes", file=sys.stderr)

if __name__ == '__main__': main()

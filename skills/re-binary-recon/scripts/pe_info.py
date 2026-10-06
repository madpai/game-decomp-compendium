#!/usr/bin/env python3
"""One-screen triage of a Windows executable: what it is, how it was built, what to expect.

usage: pe_info.py FILE [--imports] [--exports] [--json]

Reports architecture, image base, whether it carries base relocations (no relocs means
absolute addresses are stable across runs - the usual case for old 32-bit game exes), build
timestamp (identify the exact build before trusting any address), PDB path if present, Rich
header toolchain ids (which MSVC the game was built with), section table with flags and
entropy (packed/protected sections show up as high-entropy or odd names), and import DLLs.
"""
import argparse, json, math, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE

# Rich-header entries are (product id, build number, object count). Product ids are not decoded here (the id tables are
# long and version-specific); the *build number* is the compiler/linker build and is what matters for matching.
def msvc_hint(build):
    """Approximate MSVC release for a Rich-header build number (hint only; confirm against your project's compiler)."""
    exact = {8168: 'VC6 RTM (12.00.8168)', 3077: 'VS2003 / 7.1 (13.10.3077)', 50727: 'VS2005 (14.00.50727)', 30729: 'VS2008 (15.00.30729)',
             40219: 'VS2010 (16.00.40219)', 61030: 'VS2012 (17.00.61030)', 21005: 'VS2013 (18.00.21005)', 24210: 'VS2015 Update 3 (19.00.24210)'}
    if build in exact: return exact[build]
    if 24211 <= build < 27508: return 'VS2017-era (19.1x)'
    if 27508 <= build < 30000: return 'VS2019-era (19.2x)'
    if build >= 30000: return 'VS2019 16.11 / VS2022-era (19.29+/19.3x)'
    return ''

def entropy(b):
    if not b: return 0.0
    c = [0]*256
    for x in b: c[x] += 1
    n = len(b)
    return -sum(v/n * math.log2(v/n) for v in c if v)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--imports', action='store_true')
    ap.add_argument('--exports', action='store_true'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    pe = PE(a.file)
    info = {
        'file': a.file, 'size': len(pe.data), 'format': 'PE32+ (x64)' if pe.is64 else 'PE32 (x86)',
        'machine': hex(pe.machine), 'image_base': hex(pe.image_base), 'entry_rva': hex(pe.entry_rva),
        'timestamp': pe.timestamp, 'timestamp_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(pe.timestamp)) if pe.timestamp else None,
        'timestamp_hex': hex(pe.timestamp), 'has_relocations': pe.has_relocs(),
        'aslr_flag': bool(pe.dllcharacteristics & 0x40), 'dll': bool(pe.characteristics & 0x2000),
        'pdb': pe.pdb_path(), 'rich': None, 'sections': [], 'imports': {},
    }
    r = pe.rich_header()
    if r: info['rich'] = [{'product': f'prod {p:#x}', 'build': b, 'count': c, 'hint': msvc_hint(b)} for p, b, c in r if p]
    for s in pe.sections:
        raw = bytes(pe.section_bytes(s)[:1 << 20])
        info['sections'].append({'name': s.name, 'rva': hex(s.rva), 'vsize': hex(s.vsize), 'rawsize': hex(s.rsize), 'flags': ('R' if s.readable else '-') + ('W' if s.writable else '-') + ('X' if s.executable else '-'), 'entropy': round(entropy(raw), 2)})
    imps = pe.imports(); info['imports'] = {k: len(v) for k, v in imps.items()}
    if a.json:
        if a.imports: info['import_names'] = imps
        if a.exports: info['exports'] = pe.exports()
        print(json.dumps(info, indent=1)); return
    print(f"{info['file']}  {info['size']:,} bytes  {info['format']}")
    print(f"  image base {info['image_base']}  entry rva {info['entry_rva']}  timestamp {info['timestamp_hex']} ({info['timestamp_utc']})")
    print(f"  base relocations: {'YES (rebased by loader; use RVAs)' if info['has_relocations'] else 'NO (fixed address; absolute VAs are stable)'}  ASLR flag: {info['aslr_flag']}  DLL: {info['dll']}")
    if info['pdb']: print(f"  PDB: {info['pdb'][0]}  guid {info['pdb'][1]} age {info['pdb'][2]}")
    if info['rich']:
        print('  Rich header (toolchain used to build the object files):')
        for e in info['rich']: print(f"    {e['product']:<12} build {e['build']:<6} x{e['count']:<5} {e['hint']}")
    print('  sections:')
    for s in info['sections']:
        flag = '  <- high entropy (packed/encrypted?)' if s['entropy'] > 7.2 else ''
        print(f"    {s['name']:<8} rva {s['rva']:<10} vsize {s['vsize']:<10} raw {s['rawsize']:<10} {s['flags']}  H={s['entropy']}{flag}")
    print('  imports:', ', '.join(f"{k}({v})" for k, v in info['imports'].items()))
    if a.imports:
        for k, v in imps.items(): print(f"    {k}: {', '.join(v)}")
    if a.exports:
        for n, o, r_ in pe.exports(): print(f"    export {o} {n} rva {r_:#x}")

if __name__ == '__main__': main()

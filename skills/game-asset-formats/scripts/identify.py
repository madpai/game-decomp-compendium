#!/usr/bin/env python3
"""Identify game/asset file formats by magic bytes, with entropy, for a file or a whole directory tree.

usage: identify.py PATH [--recursive] [--summary] [--hex N] [--max-files N]

Why: unknown files are the first obstacle in any RE or porting job. Magic bytes + extension + entropy narrow a file to a
format family in seconds; the table below covers the containers, textures, meshes, audio, video, scripts and archives
that recur in games. High entropy (> 7.5 bits/byte) on a non-compressed type means encryption or compression you must
identify before parsing. An unknown file is reported with its first bytes so you can add a rule.
"""
import argparse, collections, math, os, struct, sys

# (offset, magic bytes, label)   order matters: longer/more specific first
MAGICS = [
 (0, b'\x89PNG\r\n\x1a\n', 'PNG image'), (0, b'\xff\xd8\xff', 'JPEG image'), (0, b'GIF8', 'GIF image'), (0, b'BM', 'BMP image (weak)'),
 (0, b'DDS ', 'DDS texture (DirectX)'), (0, b'VTF\0', 'Source VTF texture'), (0, b'\xabKTX 11\xbb\r\n\x1a\n', 'KTX texture'), (0, b'PVR\x03', 'PVR texture'),
 (0, b'RIFF', 'RIFF container (WAV/AVI/WebP; see subtype)'), (0, b'OggS', 'Ogg (Vorbis/Opus/Theora)'), (0, b'fLaC', 'FLAC audio'), (0, b'ID3', 'MP3 (ID3 tag)'),
 (0, b'FSB5', 'FMOD FSB5 sound bank'), (0, b'FSB4', 'FMOD FSB4 sound bank'), (0, b'BKHD', 'Wwise SoundBank'), (0, b'AKPK', 'Wwise package'),
 (0, b'BIKi', 'Bink video'), (0, b'KB2', 'Bink 2 video'), (0, b'SMK2', 'Smacker video'), (0, b'\x1aE\xdf\xa3', 'Matroska/WebM'),
 (0, b'BSA\0', 'Bethesda BSA archive (TES4/FO3/Skyrim)'), (0, b'BTDX', 'Bethesda BA2 archive (FO4/Starfield)'), (0, b'TES4', 'Bethesda plugin (TES4 header record)'), (0, b'TES3', 'Morrowind plugin'),
 (0, b'Gamebryo File Format', 'Gamebryo NIF mesh'), (0, b'NetImmerse File Format', 'NetImmerse NIF mesh'), (0, b';Gamebryo KFM', 'Gamebryo KFM animation manager'),
 (0, b'UnityFS', 'Unity AssetBundle (UnityFS)'), (0, b'UnityWeb', 'Unity web bundle'), (0, b'UnityRaw', 'Unity raw bundle'), (0, b'\xaf\x1b\xb1\xfa', 'Unity IL2CPP global-metadata.dat'),
 (0, b'\xc1\x83\x2a\x9e', 'Unreal .uasset/.umap (package tag 0x9E2A83C1)'), (0, b'-==--==--==--==-', 'Unreal IoStore .utoc'), (0, b'\x00asm', 'WebAssembly'),
 (0, b'IDST', 'Source MDL model'), (0, b'IDSV', 'Source VVD vertex data'), (0, b'IDPO', 'Quake MDL'), (0, b'IBSP', 'Quake 2/3 BSP'), (0, b'VBSP', 'Source BSP map'), (0, b'bsp2', 'Quake BSP2'),
 (0, b'IWAD', 'Doom IWAD'), (0, b'PWAD', 'Doom PWAD'), (0, b'PACK', 'Quake PAK archive'), (0, b'MPQ\x1a', 'Blizzard MPQ archive'), (0, b'4\x12\xaaU', 'Source VPK (0x55AA1234)'),
 (0, b'BND4', 'FromSoftware BND4 container'), (0, b'BND3', 'FromSoftware BND3 container'), (0, b'DCX\0', 'FromSoftware DCX compressed'), (0, b'FLVER', 'FromSoftware FLVER model'), (0, b'DFPN', 'FromSoftware DFPN (check)'),
 (0, b'daeh', "Halo CE map cache (header 'head' stored little-endian)"), (0, b'FORM', 'IFF/GameMaker data.win (FORM)'), (0, b'GDPC', 'Godot PCK'), (0, b'RGSSAD', 'RPG Maker RGSSAD archive'),
 (0, b'XEX2', 'Xbox 360 XEX executable'), (0, b'XBEH', 'Xbox XBE executable'), (0, b'\x7fELF', 'ELF'), (0, b'MZ', 'Windows PE (MZ)'), (0, b'\xca\xfe\xba\xbe', 'Mach-O fat / Java class'), (0, b'\xfe\xed\xfa', 'Mach-O'),
 (0, b'\x1bLua', 'Lua bytecode'), (0, b'\x1bLJ', 'LuaJIT bytecode'), (0, b'PK\x03\x04', 'ZIP/PK3/APK/JAR/PK (container)'), (0, b'7z\xbc\xaf\x27\x1c', '7-Zip'), (0, b'Rar!', 'RAR'), (0, b'\x1f\x8b', 'gzip'),
 (0, b'\x28\xb5\x2f\xfd', 'Zstandard'), (0, b'\x04\x22\x4d\x18', 'LZ4 frame'), (0, b'\xfd7zXZ', 'xz'), (0, b'SQLite format 3', 'SQLite database'), (0, b'{', 'JSON/text (weak)'), (0, b'<?xml', 'XML'), (0, b'\xef\xbb\xbf', 'UTF-8 BOM text'),
 (0, b'#!', 'script'), (0, b'XNB', 'XNA/FNA XNB content (check compression flag)'), (0, b'\x00\x01\x00\x00', 'TrueType font'), (0, b'OTTO', 'OpenType (CFF) font'), (0, b'wOFF', 'WOFF font'), (0, b'\xff\xfe', 'UTF-16LE text (BOM)'), (0, b'\xfe\xff', 'UTF-16BE text (BOM)'),
 (0, b'\x00\x00\x01\x00', 'Windows ICO (or TGA; by extension)'), (0, b'\x00\x00\x02\x00', 'Windows CUR (or TGA; by extension)'),
 (0, b'ARC\x00', 'archive (generic ARC)'), (0, b'CPK ', 'CRI CPK archive'), (0, b'@UTF', 'CRI UTF table'), (0, b'HCA\0', 'CRI HCA audio'), (0, b'NPCK', 'archive (NPCK)'),
 (0, b'BIGF', 'EA BIG archive'), (0, b'BIG4', 'EA BIG4 archive'), (0, b'SARC', 'Nintendo SARC archive'), (0, b'Yaz0', 'Nintendo Yaz0 compressed'), (0, b'U8\x2d', 'Nintendo U8 archive'),
]
def entropy(b):
    if not b: return 0.0
    c = collections.Counter(b); n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())

def identify(path, hexn=0):
    with open(path, 'rb') as f: head = f.read(64 * 1024)
    size = os.path.getsize(path)
    label = None
    for off, magic, lab in MAGICS:
        if head[off:off + len(magic)] == magic: label = lab; break
    ext = os.path.splitext(path)[1].lower()
    if label and ('or TGA' in label): label = 'TGA image (no magic; by extension)' if ext == '.tga' else label.split(' (')[0]
    if label and label.startswith('RIFF') and len(head) >= 12:
        label = {b'WAVE': 'WAV audio (RIFF)', b'AVI ': 'AVI video (RIFF)', b'WEBP': 'WebP image (RIFF)'}.get(head[8:12], label)
    if not label and head[:2] == b'\xff\xfb': label = 'MP3 frame'
    if not label:
        sample = head[:4096]
        if sample and sum(1 for c in sample if 32 <= c < 127 or c in (9, 10, 13)) / len(sample) > 0.88: label = 'text (ASCII/UTF-8)'
        elif ext == '.tga': label = 'TGA image (no magic; by extension)'
        elif ext == '.vpk': label = 'Source VPK data chunk (headerless; pairs with *_dir.vpk)'
    if label and label.startswith('Source VTF') and ext == '.vpk': label = 'Source VPK data chunk (starts inside a VTF; pairs with *_dir.vpk)'
    h = entropy(head)
    return {'path': path, 'size': size, 'type': label or 'unknown', 'ext': ext, 'entropy': round(h, 2), 'head': head[:hexn if hexn else 16].hex(' ')}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('path'); ap.add_argument('--recursive', '-r', action='store_true')
    ap.add_argument('--summary', action='store_true'); ap.add_argument('--hex', type=int, default=0); ap.add_argument('--max-files', type=int, default=5000)
    a = ap.parse_args()
    files = []
    if os.path.isdir(a.path):
        for dp, dn, fn in os.walk(a.path):
            for f in fn: files.append(os.path.join(dp, f))
            if not a.recursive: break
    else: files = [a.path]
    files = files[:a.max_files]
    res = [identify(p, a.hex) for p in files if os.path.isfile(p)]
    if a.summary or len(res) > 40:
        by = collections.defaultdict(list)
        for r in res: by[(r['type'], r['ext'])].append(r)
        for (t, e), rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
            avg_h = sum(r['entropy'] for r in rs) / len(rs)
            print(f"{len(rs):5d}  {t:<48} {e or '-':<8} avg entropy {avg_h:4.1f}  e.g. {rs[0]['path']}")
        unk = [r for r in res if r['type'] == 'unknown']
        if unk: print(f"# {len(unk)} unknown; sample heads: " + '; '.join(f"{os.path.basename(r['path'])}={r['head']}" for r in unk[:5]))
    else:
        for r in res: print(f"{r['type']:<48} {r['size']:>10}  H={r['entropy']:<5} {r['path']}" + (f"\n    {r['head']}" if a.hex or r['type'] == 'unknown' else ''))

if __name__ == '__main__': main()

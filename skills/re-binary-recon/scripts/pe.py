#!/usr/bin/env python3
"""Minimal dependency-free PE reader shared by the other scripts in this folder.

Handles PE32 and PE32+. Memory-maps the file, converts between RVA / VA / file offset,
and exposes sections, imports, exports, the debug directory (PDB path) and the base
relocation table. Not a validator: it is meant for analysing binaries you own, fast.
"""
import mmap, struct, sys

class Section:
    def __init__(self, name, vsize, rva, rsize, roff, flags):
        self.name, self.vsize, self.rva, self.rsize, self.roff, self.flags = name, vsize, rva, rsize, roff, flags
    @property
    def executable(self): return bool(self.flags & 0x20000000)
    @property
    def writable(self): return bool(self.flags & 0x80000000)
    @property
    def readable(self): return bool(self.flags & 0x40000000)
    def __repr__(self): return f"<{self.name} rva={self.rva:#x} vsize={self.vsize:#x} raw={self.roff:#x}+{self.rsize:#x}>"

class PE:
    def __init__(self, path):
        self.path = path
        f = open(path, 'rb')
        self.data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        d = self.data
        if d[:2] != b'MZ': raise ValueError('not an MZ executable')
        self.e_lfanew = struct.unpack_from('<I', d, 0x3c)[0]
        if d[self.e_lfanew:self.e_lfanew+4] != b'PE\0\0': raise ValueError('no PE signature')
        o = self.e_lfanew + 4
        (self.machine, nsec, self.timestamp, _, _, optsize, self.characteristics) = struct.unpack_from('<HHIIIHH', d, o)
        o += 20
        self.magic = struct.unpack_from('<H', d, o)[0]
        self.is64 = self.magic == 0x20b
        if self.is64:
            self.entry_rva = struct.unpack_from('<I', d, o+16)[0]
            self.image_base = struct.unpack_from('<Q', d, o+24)[0]
            self.size_of_image = struct.unpack_from('<I', d, o+56)[0]
            ndirs = struct.unpack_from('<I', d, o+108)[0]; dirs_off = o + 112
        else:
            self.entry_rva = struct.unpack_from('<I', d, o+16)[0]
            self.image_base = struct.unpack_from('<I', d, o+28)[0]
            self.size_of_image = struct.unpack_from('<I', d, o+56)[0]
            ndirs = struct.unpack_from('<I', d, o+92)[0]; dirs_off = o + 96
        self.dllcharacteristics = struct.unpack_from('<H', d, o+70)[0]
        self.dirs = [struct.unpack_from('<II', d, dirs_off + 8*i) for i in range(min(ndirs, 16))]
        so = o + optsize
        self.sections = []
        for i in range(nsec):
            nm, vs, rva, rs, ro = struct.unpack_from('<8sIIII', d, so + 40*i)[:5]
            fl = struct.unpack_from('<I', d, so + 40*i + 36)[0]
            self.sections.append(Section(nm.rstrip(b'\0').decode('latin1'), vs, rva, rs, ro, fl))
        self.ptr = 8 if self.is64 else 4

    # -- address conversion ---------------------------------------------------
    def rva_to_off(self, rva):
        for s in self.sections:
            if s.rva <= rva < s.rva + max(s.vsize, s.rsize):
                off = rva - s.rva
                return s.roff + off if off < s.rsize else None
        if rva < self.sections[0].rva: return rva  # header
        return None
    def va_to_rva(self, va): return va - self.image_base
    def rva_to_va(self, rva): return rva + self.image_base
    def section_of_rva(self, rva):
        for s in self.sections:
            if s.rva <= rva < s.rva + max(s.vsize, s.rsize): return s
    def section_of_va(self, va): return self.section_of_rva(va - self.image_base)
    def read_rva(self, rva, n):
        off = self.rva_to_off(rva)
        return None if off is None else bytes(self.data[off:off+n])
    def read_va(self, va, n): return self.read_rva(va - self.image_base, n)
    def u32(self, va):
        b = self.read_va(va, 4); return None if b is None or len(b) < 4 else struct.unpack('<I', b)[0]
    def cstr_rva(self, rva, maxlen=512):
        off = self.rva_to_off(rva)
        if off is None: return None
        end = self.data.find(b'\0', off, off+maxlen)
        return bytes(self.data[off:end if end >= 0 else off+maxlen]).decode('latin1')
    def section_bytes(self, s): return self.data[s.roff:s.roff+s.rsize]
    def in_image(self, va): return self.image_base <= va < self.image_base + self.size_of_image
    def in_exec(self, va):
        s = self.section_of_va(va); return bool(s and s.executable)

    # -- directories ----------------------------------------------------------
    def imports(self):
        rva, size = self.dirs[1] if len(self.dirs) > 1 else (0, 0)
        out = {}
        if not rva: return out
        p = rva
        while True:
            raw = self.read_rva(p, 20)
            if not raw or len(raw) < 20: break
            oft, _, _, name, ft = struct.unpack('<IIIII', raw)
            if not name: break
            dll = self.cstr_rva(name)
            names = []
            t = oft or ft
            i = 0
            while True:
                ent = self.read_rva(t + i*self.ptr, self.ptr)
                if not ent: break
                v = int.from_bytes(ent, 'little')
                if v == 0: break
                ordflag = 1 << (63 if self.is64 else 31)
                if v & ordflag: names.append(f"#{v & 0xffff}")
                else: names.append(self.cstr_rva((v & 0x7fffffff) + 2))
                i += 1
            out[dll] = names
            p += 20
        return out
    def exports(self):
        rva, size = self.dirs[0]
        if not rva: return []
        hdr = self.read_rva(rva, 40)
        (_, _, _, _, base, nfunc, nnames, aof, aon, aoo) = struct.unpack('<IIHHIIIIII', hdr)[:10]
        res = []
        for i in range(nnames):
            nrva = struct.unpack('<I', self.read_rva(aon + 4*i, 4))[0]
            ordi = struct.unpack('<H', self.read_rva(aoo + 2*i, 2))[0]
            frva = struct.unpack('<I', self.read_rva(aof + 4*ordi, 4))[0]
            res.append((self.cstr_rva(nrva), base + ordi, frva))
        return res
    def pdb_path(self):
        rva, size = self.dirs[6] if len(self.dirs) > 6 else (0, 0)
        for i in range(size // 28):
            e = self.read_rva(rva + 28*i, 28)
            if not e: break
            typ, sz, _, ptr = struct.unpack_from('<I', e, 12)[0], struct.unpack_from('<I', e, 16)[0], 0, struct.unpack_from('<I', e, 24)[0]
            if typ == 2 and ptr:
                blob = self.data[ptr:ptr+sz]
                if blob[:4] == b'RSDS':
                    return bytes(blob[24:]).split(b'\0')[0].decode('latin1'), bytes(blob[4:20]).hex(), struct.unpack_from('<I', blob, 20)[0]
        return None
    def has_relocs(self): return bool(self.dirs[5][0]) if len(self.dirs) > 5 else False
    def reloc_rvas(self):
        """Set of RVAs that carry a base relocation (useful to wildcard operands in signatures)."""
        rva, size = self.dirs[5]
        out = set()
        if not rva: return out
        p, end = rva, rva + size
        while p < end:
            hdr = self.read_rva(p, 8)
            if not hdr or len(hdr) < 8: break
            page, bsz = struct.unpack('<II', hdr)
            if bsz < 8: break
            for i in range((bsz - 8) // 2):
                v = struct.unpack('<H', self.read_rva(p + 8 + 2*i, 2))[0]
                if v >> 12 in (3, 10): out.add(page + (v & 0xfff))
            p += bsz
        return out
    def rich_header(self):
        d = self.data
        end = d.find(b'Rich', 0, self.e_lfanew)
        if end < 0: return None
        key = struct.unpack_from('<I', d, end + 4)[0]
        i = end - 4
        vals = []
        while i >= 0x80:
            v = struct.unpack_from('<I', d, i)[0] ^ key
            if v == 0x536e6144: break  # 'DanS'
            vals.append(v); i -= 4
        vals.reverse()
        # entries are (comp_id, count) pairs after three padding dwords
        pairs = [(vals[j] , vals[j+1]) for j in range(3, len(vals) - 1, 2)]
        return [(((cid >> 16) & 0xffff), cid & 0xffff, cnt) for cid, cnt in pairs]  # (prod_id, build, count)

def main():
    for p in sys.argv[1:]:
        pe = PE(p)
        print(p, 'PE32+' if pe.is64 else 'PE32', hex(pe.image_base), pe.sections)

if __name__ == '__main__':
    main()

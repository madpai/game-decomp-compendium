# Parser safety and testing checklist

Sources: unity-rs `AGENTS.md` (a very explicit, agent-oriented contract; read in the corpus), binrw README, objdiff AGENTS.md testing notes, universal-modder techniques.

## Design rules
1. **Untrusted input**: file bytes, archive/path names, callbacks, schemas.
2. **Checked arithmetic/conversions** for every input-derived offset, size, count, alignment, stride, capacity.
3. **Bounded work**: limits on each file and cumulatively on input, allocation, decompression, traversal depth, strings, metadata and output. Prefer immutable source-backed region views and bounded streaming writers over whole-file copies and shared mutable cursors. Use fallible reservation before growing `Vec`/`String`/maps from input counts.
4. **Complete-or-reject**: validate a complete known layout; an unverified tail or version gate is rejected, not partially parsed (one sanctioned exception in unity-rs: above a verified ceiling, attempt the newest known layout and fail with an explicit `Unsupported` naming the attempt).
5. **Error families stay distinct**: malformed bytes (`InvalidData`), missing verified support (`Unsupported`), resource limits, I/O.
6. **No silent fallbacks** turning corrupt/unknown input into plausible output; never weaken a limit or test to make a sample pass.
7. **Smallest coherent change**; keep CLI/library/bindings behaviour aligned; no unsafe in parsing crates (forbid at workspace level; audit any glue).
8. **Licensing hygiene**: third-party notices; no proprietary decoder binaries or embedded game keys; optional capabilities (Oodle, ACL...) behind caller-supplied data/adapters.

## Test strategy
- Fixtures for every claimed version; a private opt-in corpus harness for real assets (never committed); a differential oracle against a managed/reference implementation when available (`oracle/` directory pattern).
- Snapshot tests (`insta`) for stable outputs; property tests (`proptest`) for round trips and invariants; fuzzing (`cargo-fuzz`, afl) for hostile bytes; benchmarks (`criterion`) for regressions.
- Whole-corpus assertions: parse every stock file, assert structural invariants (counts match, offsets in range, no unread bytes), print per-type statistics.
- Round trip: decode -> encode -> decode equals original (or within a stated error for lossy codecs).

## binrw patterns (Rust)
Declarative `#[derive(BinRead, BinWrite)]` with `#[br(magic = b"BSA\0")]`, endianness, `pad_before/after`, `align`, `assert`/`validate`, `FilePtr`-style offset indirection, `NullString`, `count = n`, `map`, custom parsers via free functions; works with any `Read + Seek`. Use for fixed-layout structs; hand-write loops for variable-length run-length or bit-packed streams (animation channels), where bounds checks matter more than brevity.

## Python quick rules
`struct.unpack_from` with explicit little-endian; assert `offset + size <= len(buf)` before slicing; `memoryview` for big files; validate against a second parse path; keep the parsing function pure so a test can feed it fixtures.

## Boundary and count errors (the last record goes missing or is garbage)
General failure classes, **[inferred]**: no incident of this kind is recorded in the compendium yet, so add an experiment or gotcha the first time you hit one (`hub.py template experiment`). Symptom search: `hub.py diagnose "archive parser misses a final record"`.
- Loop bound off by one (`range(n - 1)`, `< n - 1`), or a count taken from a header field that excludes a sentinel or terminator entry.
- Entry size computed as `next.offset - this.offset`: the last entry has no next. Use the section or file end, or an explicit size field.
- A trailing record or table that is not padded or terminated like the earlier ones (alignment, NUL-terminated name table, a final chunk shorter than the block size).
- Offsets relative to different bases in different tables (file start, header end, data start). The last entries expose the mix-up when earlier ones happen to coincide.
- Two counting conventions: a serialized triangle strip of length n holds n-2 triangles, and a loader that drops degenerate steps keeps fewer (1,288 serialized versus 575 kept on one Oblivion stair mesh). Say which count you mean before calling a count a bug.
- A short read or truncated final block treated as end of file. Fail loudly instead.

Oracles that find these: entry count equals both the header's count and an independent tool's listing; the sum of entry sizes plus headers equals the file size (no gaps, no overlap); parse, write, byte-compare round trip (`technique:round-trip-oracle`); size and hash of the last few entries against a known-good extractor; fuzz with files truncated at every entry boundary.

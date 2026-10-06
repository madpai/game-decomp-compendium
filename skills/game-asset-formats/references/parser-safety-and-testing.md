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

# Pipeline, file formats and commands

Contents: 1 the flow · 2 dtk-style config · 3 objdiff.json and reports · 4 reccmp (x86 PE) · 5 ReproBit-style verification · 6 splitting, relocations, shiftability · 7 Ghidra headless as the analysis backend · 8 command cheat sheet

Sources (all read in the local clone corpus): dtk-template conventions as used by FNV/NFSMW/Halo decomps, objdiff README + `config.schema.json`, isle's `reccmp-project.yml` and `reprobit.toml`, decompedia's `resources/decomp-intro.md`, AVP2/Thief3/LEGOLAND/BW1 docs.

## 1. The flow in one picture

```
original binary ──split (dtk/splat/csplit/Ghidra)──► per-TU target objects (.o)   ← "what the original compiler emitted"
        │                                                  ▲ compare per symbol (objdiff / asm-differ / reccmp)
        └── symbols.txt + splits.txt + config ──► configure.py ──► build.ninja ──► your source → compiler → base objects
                                                                          └─► link ─► executable ─► sha1/sha256 == original ?
```
Why objects, not executables: a compiler sees one translation unit at a time; the linker glues units together and rewrites call/data operands into final addresses (relocations). Un-linking (splitting) restores symbolic references so a function compiled from your source can be compared with the original's *regardless of where it ended up*. Inlining decisions are per-TU, which is why split boundaries matter: if two functions that inlined into each other are split into different TUs, neither will ever match.

## 2. dtk-style project files

`symbols.txt` (one symbol per line; comments `//` or `#` are not preserved on rewrite):
```
?CamJointPositions@DancerSkeleton@@UBAXPAVVector3@@@Z = .text:0x8251D260; // type:function size:0x14 scope:global
```
fields: `name = section:address; // type:(function|object|label) size:0x.. scope:(global|local|weak) align:N data:(byte|2byte|4byte|8byte|float|double|string|wstring|string_table|wstring_table)`. Use mangled names for C++ so objdiff pairs by name. Scope `weak` = header-defined/inline, `local` = file-static.

`splits.txt` (file → section address ranges; the file need not exist yet):
```
path/to/file.cpp:
	.text       start:0x8249D270 end:0x824A2678
	.rdata      start:0x82044A58 end:0x82045A70
	.data       start:0x82F0D998 end:0x82F0D9F0
	.data       start:0x82F60C88 end:0x82F60D88 rename:.bss
```
The path matches an entry in `configure.py` (compiler flags, status). Order of splits = original link order, which matters for data/bss layout and for static-initialiser order.

`config.json` (progress categories + flag sets) and `objects.json` (which TUs are `Matching`, `NonMatching`, `Equivalent`, `MISSING`, with per-object cflags and compiler version):
```json
"cflags": { "base": {"flags": ["/nologo","/c","/GR","/O1"]}, "engine": {"base":"base","flags":["/O2"]} }
"main": { "progress_category": "game", "mw_version": "X360/16.00.11886.00", "cflags": "base",
          "objects": { "path/to/file1.cpp": "MISSING" } }
```
Build status semantics (BW1): `Matching` is linked into the final exe; `NonMatching` is work in progress and not linked; `Equivalent` is behaviourally equal but only linked with `--non-matching`.

`configure.py` is the single generator: reads config, writes `build.ninja` and `objdiff.json`; `ninja` builds and reports progress. Keep generated files out of git.

## 3. objdiff

`objdiff.json` at the repo root (generate it from configure.py):
```json
{ "custom_make": "ninja", "build_target": false, "build_base": true,
  "watch_patterns": ["*.c","*.cpp","*.h","*.inc","*.s","*.py","*.yml","*.txt","*.json"], "ignore_patterns": ["build/**/*"],
  "units": [ { "name": "main/MetroTRK/mslsupp", "target_path": "build/asm/MetroTRK/mslsupp.o",
               "base_path": "build/src/MetroTRK/mslsupp.o", "metadata": {"complete": false} } ] }
```
- **target** = expected object (from the original), **base** = built from your source (omit if no source yet). `metadata.auto_generated` hides a unit from the sidebar but keeps it in reports; `metadata.complete` marks linked/complete.
- Schema: `https://raw.githubusercontent.com/encounter/objdiff/main/config.schema.json`.
- `objdiff-cli diff` is the TUI; `objdiff-cli report generate` emits the protobuf/JSON progress report used by decomp.dev (`objdiff-core/protos/report.proto`).
- Agents cannot use the GUI. Wrap `objdiff-cli` in a small script that prints target-left/ours-right with markers (BW1's `decomp-diff.py`: ` ` match, `~` operand differs, `|` opcode differs, `>` only ours, `<` only target; `-s nonmatching -t function` filters; `--strict` compares relocation identities; `--no-collapse` shows every line). That wrapper plus build-one-object-only (`ninja build/.../Foo.o`, ~1-2 s) is the fast inner loop; full `ninja` relinks and regenerates the report every time and is for batch verification.
- Relocation comparison modes matter: default `data_value`-style comparison forgives address differences if bytes at the resolved address agree; `--strict` includes relocation identity and addends. Report which you used.
- decomp.dev: reports are generated in CI and uploaded; its GitHub app comments progress deltas on PRs. Integration for a non-dtk project: build "target" objects (for splat: `make_full_disasm_for_code`), build "base" objects from source, run `objdiff-cli report generate`, upload.

## 4. reccmp (x86 PE, address-annotated source)

Used by isle, LEGOLAND, AVP2. Source carries markers; reccmp compiles nothing itself, it compares your built binary + PDB (or map) against the original per function, normalising addresses.
```cpp
// FUNCTION: LEGO1 0x10001234          matched function at that address in module LEGO1
// STUB: LEGO1 0x10001300              written but not matching yet (excluded from % )
// GLOBAL: LEGO1 0x10102000            data symbol
// VTABLE: LEGO1 0x100d4a00            vtable
// LIBRARY: LEGO1 0x1008f000           library code (not game source)
// SYNTHETIC: LEGO1 0x...              compiler-generated thunk
// STRING: LEGO1 0x...                 string literal (also reccmp-strings.csv / reccmp-globals.csv data sources)
```
`reccmp-project.yml` declares targets: `filename`, `source-root`, expected `hash: {sha256: ...}`, optional `data-sources`, report ignore lists, and Ghidra sync options. Multiple modules (EXE + DLLs) are separate targets; shared headers affect all.
Annotation hygiene (BW1 variant): each declaration in headers carries an address comment line holding *only* addresses (`// BW1W120 0054cbd0 BW1M119 010cca10`; `inlined`, `null`, `purecall` allowed in place of an address) with notes on their own line; CI checks the format (`check_addr_comments.py`).

## 5. ReproBit-style whole-file verification (isle)

`reprobit.toml` declares per-target `artifact` (what you built) and `oracle` (the original file), a toolchain adapter/profile with a lock file (compiler binary hashes), a `verifier.kind = "literal"` (byte-for-byte), and `authenticity.policy = "clean"` (no oracle bytes smuggled in). Idea to copy: make "the whole executable reproduces" a CI check with the compiler pinned by hash, separate from per-function percentages.

## 6. Splitting, relocations, shiftability

- Splitting must turn hard-coded addresses back into symbolic references; it is only provably right when the whole program matches. dtk detects relocations automatically and sometimes misses or invents some: use `noreloc` on data that merely looks like a pointer.
- Float constants give split hints under Metrowerks (the linker does not dedupe `0.0f`/`1.0f` across TUs, so repeated constants mark TU starts); string pools and `.ctors` order also help.
- "Shiftability" = being able to add/remove code without breaking hard-coded pointers (needed for mods). Static variables have fixed addresses; relative pointer trees rooted in malloc are fine. (Decompedia's page is an unreviewed draft: treat as orientation, not authority.)
- LTO/whole-program optimisation defeats per-TU matching (why BotW 1.6.0 is hard). Prefer pre-LTO builds.

## 7. Ghidra headless as the analysis backend (Thief3 pattern)

Keep a scripted Ghidra project per binary: bootstrap (import, analyse, apply names from `symbols.txt`), then headless scripts such as `Decompile.java <addr> [refs:<addr>]` (decompile the function, or every function referencing an address) and `Disassemble.java <addr>[+count]` (annotates calls with callee names). Cache decompiles for the queue head so workers get them in their context packet. Write names back to `symbols.txt` and re-apply with a `names` command so Ghidra and the repo cannot drift (AVP2 also syncs renames from source back into Ghidra).

## 8. Command cheat sheet

```sh
python configure.py [--wrapper wibo] [--objdiff objdiff-cli]   # generate build.ninja + objdiff.json
ninja                                  # build, link, report progress
ninja build/<ver>/src/path/File.o      # inner loop: one object only
objdiff-cli diff -u <unit> <symbol>    # TUI diff;  objdiff-cli report generate -o report.json
python tools/decomp-diff.py --unit X -d "Class::Method"   # agent-friendly text diff (project-local wrapper)
reccmp-reccmp --target LEGOLAND [--verbose 0x004015c0]    # x86 per-function verification
sha1sum -c build.sha1                  # final file-level check
```

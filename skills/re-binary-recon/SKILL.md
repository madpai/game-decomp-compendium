---
name: re-binary-recon
description: Fast, dependency-free static reconnaissance of Windows game executables and DLLs (PE32/PE32+): triage a binary, recover C++ class names/vtables/inheritance from MSVC RTTI, find the code that uses a string ("debug string -> function"), build version-robust byte signatures (AOB), identify the compiler/toolchain, and decide what to name or hook first. Use whenever you must understand an unfamiliar game exe/dll, find where a feature lives, map engine classes (Gamebryo/NiNode, Unreal, Unity, Source), prepare symbols for Ghidra/IDA, check whether a binary has RTTI or relocations, or verify a claim about what an executable does. Includes tested scripts (pe_info, rtti_scan, string_xrefs, aob_scan) and the evidence-level discipline that keeps RE trustworthy.
---

# Binary recon for game executables

Goal: in minutes, know what a binary is, which engine classes it contains, and where to start reading, using evidence you can re-check. All scripts are pure Python 3 (no pefile/capstone), read-only, and were tested on x86 and x64 MSVC binaries (Oblivion.exe 7.9 MB: RTTI scan 0.15 s; Half-Life `hw.dll`; a Unity player DLL x64).

## The five-step recon

1. **Triage**: `python3 scripts/pe_info.py FILE [--imports]`
   - *PE timestamp* is your build id: record it and refuse to apply addresses to any other build.
   - *Base relocations: NO* (typical for 2000s x86 games) means absolute VAs are stable across runs, so addresses from static analysis can be hard-coded for that exact build. *YES* means use RVAs and the module base at runtime.
   - *Rich header* lists the MSVC product/build ids that built the object files (compiler identification for matching work).
   - Section table: a high-entropy section with an odd name (`.bind`, `.text1`, `.steam`) that contains the entry point means the exe is wrapped by a protection stub. Analyse only what is readable; do not attempt to defeat DRM/anti-tamper (see `decomp-matching-workflow/references/legal-and-etiquette.md`). The unencrypted `.text/.rdata/.data` of such wrappers are often still analysable (Steam-wrapped Oblivion.exe is).
   - Imports tell you subsystems (d3d9/d3dx9_xx, dinput8, dsound, winmm, ws2_32, bink) and hook points.
2. **Class map**: `python3 scripts/rtti_scan.py FILE [--grep REGEX] [--format tsv|json|ghidra|idc]`
   - Recovers every class with an MSVC vtable: vtable VA, slot count, multiple-inheritance sub-vtables (col_offset != 0), the full base-class list. Empty result = built `/GR-` or stripped: say so, do not guess.
   - `--format ghidra|idc` emits names to apply in your disassembler. Slot count is a cheap complexity metric (Oblivion `Actor` has 239 virtual slots, `TESObjectREFR` 105).
3. **Feature pivot**: `python3 scripts/string_xrefs.py FILE --grep 'REGEX' [--wide]`
   - Lists strings and their references (x86 absolute operands; x64 RIP-relative; data pointer tables). `approx func` is the first byte after the previous padding run: a place to start reading, not a boundary. Config keys, `%s_%s_%08X`-style format strings, assert messages and script-command names are the best pivots. A string referenced only from *data* is usually a table (command table, factory list, property table): follow it.
4. **Stable handles**: `python3 scripts/aob_scan.py FILE make 0xVA --len 64` then `find "<pattern>"`
   - Builds a signature with call/jump displacements and in-image pointers wildcarded and reports the shortest unique prefix. Re-verify on each target build. This is how `fromsoftware-rs`' binary mapper keeps RVAs valid across patches (TOML profile + RVA tests).
5. **Write down what you know with its evidence level**: *static* (read from code/data/strings), *verified* (observed at runtime, or confirmed by an independent second source such as another caller, a debug string, a sibling-platform symbol, or a known struct layout). Do not upgrade without a second source. Keep a journal (what, where, how confirmed, how to re-check).

## Decide what to do next
- Understand/port a subsystem: pivot from strings to the function, name it, read callers/callees, then validate against real data with an oracle (see `references/rtti-vtables-and-oracles.md`).
- Hook it: go to `game-hooking-patterns` (single-player/offline only).
- Match it byte-for-byte: go to `decomp-matching-workflow`.
- Parse its data files: go to `game-asset-formats`; Bethesda specifics are in `bethesda-gamebryo-re`.

## Heavy tools (when the scripts are not enough)
Ghidra (headless scripts for decompile/disassemble/rename; GhidraMCP/pyghidra-mcp/ReVa for agents), IDA (+ MCP), x64dbg, Cheat Engine/ReClass.NET (live structs; offline single-player only), Frida, RenderDoc (graphics passes), iced-x86 (decode/format/assemble from Rust/Python), `pelite`/`goblin`/`object` (Rust parsers), Il2CppDumper/Cpp2IL (Unity IL2CPP), Dumper-7/UE4SS dumpers (Unreal reflection). Read `references/signatures-versioning-and-tools.md`.

## Guardrails
- Analyse binaries the user owns. Keep decompiler output, disassembly and extracted data out of repositories; commit your own notes, scripts and small documenting snippets.
- Never attach debuggers/scanners to online games with anti-cheat; never bypass anti-cheat or DRM.
- The scripts read files only. A claim about runtime behaviour needs a runtime oracle, not another static guess.

## Files
- `scripts/pe.py` (library), `pe_info.py`, `rtti_scan.py`, `string_xrefs.py`, `aob_scan.py`
- `references/rtti-vtables-and-oracles.md`: how RTTI/vtables/COLs are laid out, recognising conventions, strings and tables, oracle patterns.
- `references/signatures-versioning-and-tools.md`: AOB/RVA practice, version guards, tool menu with MCP options, Rust RE crates.

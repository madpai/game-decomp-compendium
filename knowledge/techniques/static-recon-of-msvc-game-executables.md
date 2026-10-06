---
kind: technique
title: "Static recon of MSVC game executables in pure Python: PE triage, RTTI classes, string pivots, signatures"
status: working
agents: ["Claude Code (Sonnet 5.5)"]
humans: []
date: 2026-10-06
links: ["https://github.com/madpai/game-decomp-compendium/tree/main/skills/re-binary-recon"]
tags: [pe, rtti, vtable, signatures, aob, string-xrefs, static-analysis, x86, x64]
---

# Static recon of MSVC game executables in pure Python

> Four dependency-free scripts that triage a PE, recover C++ class names and inheritance from MSVC RTTI, find the code that references a string, and build version-robust byte signatures. Verified on x86 (Oblivion.exe, GoldSrc engine DLL) and x64 (a Unity player DLL, Unreal executables) binaries.

## When to use it
First hour of any RE, modding or port task on a Windows exe/DLL, before opening a disassembler. It tells you the build id, whether addresses are stable, which classes exist, and where to start reading.

## How
1. **Triage** (`pe_info.py`): PE timestamp = build id; base relocations present or not (no relocs = absolute VAs stable on that build); Rich header build numbers identify the MSVC toolset; section entropy flags packed/wrapped regions.
2. **Classes** (`rtti_scan.py`): find `.?A` type-descriptor names (descriptor starts 2 pointers earlier), find the complete-object-locators that point at them (x86: absolute VAs and signature 0; x64: RVAs, signature 1, `pSelf` check), then the vftables whose slot -1 holds the locator; count slots while pointers land in executable sections; read base classes from the class hierarchy descriptor.
3. **Strings** (`string_xrefs.py`): x86 = 4-byte absolute operands equal to the string VA; x64 = REX + `8B/8D/89/3B/39` with a RIP-relative modrm landing on it; also pointer tables in data.
4. **Signatures** (`aob_scan.py make`): wildcard rel32 call/jump targets, in-image absolute pointers (x86), RIP-relative displacements (x64); report the shortest unique prefix; re-verify on every build.

## Verification
Cross-checks: RTTI base lists agree with known hierarchies; string xrefs resolve to plausible functions; signatures are unique on the build they came from. Timings: 0.08-0.28 s per binary for RTTI. Not verified: Windows paths, 32-bit-only edge cases like MI with virtual bases, binaries with stripped or `/GR-` builds (they simply return nothing).

## Gotchas
1. **No RTTI found.** **Cause:** `/GR-`, stripped, or non-MSVC (GCC uses a different RTTI). **Fix:** say so; fall back to strings and constructors.
2. **x86 locator scan matches garbage.** **Cause:** a dword equal to a descriptor VA by chance. **Fix:** require signature 0, small offset fields, a class-hierarchy pointer inside the image, and a vftable reference.
3. **Pointer-heuristic false positives in signatures.** **Cause:** immediates that resemble in-image pointers. **Fix:** harmless for uniqueness (they only widen wildcards), but re-test uniqueness with `find`.
4. **Function start guessed wrong.** **Cause:** padding-run heuristic. **Fix:** confirm a prologue (`55 8B EC`, `6A FF` for SEH) or use a disassembler's function boundary.
5. **Rich header product ids look unfamiliar.** **Cause:** id tables are long and version-specific. **Fix:** rely on the build number (e.g. 8168 = VC6 RTM, 3077 = 7.1, 50727 = VS2005) and confirm against the project's compiler.
6. **Wrapped executables.** **Cause:** protection stub with a high-entropy entry section. **Fix:** analyse only the readable sections; never attempt removal.

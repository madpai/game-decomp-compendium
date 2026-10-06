# RTTI, vtables, strings, tables, and oracles

## MSVC RTTI layout (what `rtti_scan.py` relies on)
```
TypeDescriptor        { void* pVFTable; void* spare; char name[] }       name = ".?AVNiNode@@" (class) | ".?AU" struct | ".?AT" union | ".?AW4" enum
CompleteObjectLocator { sig, offset, cdOffset, pTypeDescriptor, pClassHierarchyDescriptor [, pSelf] }
vftable               [ pCOL ][ slot0 ][ slot1 ] ...                      the COL pointer is at vftable[-1]
ClassHierarchyDesc    { sig, attributes, numBases, pBaseClassArray }
BaseClassDescriptor   { pTypeDescriptor, numContainedBases, PMD{mdisp,pdisp,vdisp}, attributes, pCHD }
```
x86: pointers are absolute VAs and `sig == 0`. x64: 32-bit RVAs, `sig == 1`, extra `pSelf` RVA. Multiple inheritance = several COLs/vftables with different `offset` (the `this` adjustment). Demangling `.?AVFoo@Bar@@` gives `Bar::Foo`; templates start `?$`.

Uses: (1) class names for every vftable; (2) the linearised base list shows inheritance without reading code (e.g. in Oblivion.exe `PlayerCharacter` -> `Character` -> `Actor` -> `MobileObject` -> `TESObjectREFR` -> `TESForm`); (3) slot counts bound the size of interfaces; (4) vtable addresses are anchors: constructors store them, so xrefs to a vtable VA find constructors and `new` sites; (5) hooking virtuals by slot index is version-robust within a build family.

Not every binary has RTTI: `/GR-` removes it (Thief 3's engine fork), release builds of some middleware strip names. RTTI present in a retail exe is a gift: names for hundreds to thousands of classes without debug info (Oblivion.exe: 1,715 vtables / 1,482 classes including `TESQuest`, `TESTopicInfo`, `Script`, `NiNode`, SpeedTree shader classes).

## Recognising calling conventions and virtuals (x86 MSVC)
- `__thiscall`: `this` in ECX; callee cleans args (`ret N`). Decorated names `?M@C@@QAEHH@Z` (`QAE` = public member thiscall).
- Virtual call: `mov eax,[ecx]; call [eax+4*k]`; scalar deleting destructor is slot 0 (called with arg 1).
- Hooking requires matching the convention; a free C function replacing a thiscall gets a corrupt `this`.
- `cmp eax,N; ja default; jmp [eax*4+table]` is a dense switch; jump tables sit after the function.
- Exception frames (`push -1; push handler; mov eax,fs:[0]`) mean locals with destructors: functions with these are usually "real" game code, not trivial thunks.

## Strings as pivots
Typical high-value strings: config/INI keys (read through a getter taking a section and key literal: find the getter's callers), debug-name strings next to global constructors (UE2 `TArray` debug names let Thief 3 name 209 globals: push name; push elem size; mov ecx, global; call ctor), log/assert formats (`...file %s on line %i... form %08X`), file-path/extension tables (`sFileTypeGame:Voice`, `mp3`, `wav`, `lip`), script command names (a data table of 40-byte records in Oblivion.exe), resource paths. Search ASCII and UTF-16 (`--wide`). When a string is referenced only from data, the data is a table: dump the table (stride = distance between successive references), then name each entry.

## Tables
Command tables, factory/registration lists and property tables are arrays of fixed-size records containing name pointers. Find one name (e.g. `GetStage`), look at who references it from data, compute the stride from consecutive entries, and read every record. Verify the layout on several entries before trusting field meanings (parameter-type ids, opcodes, flags). This is how Oblivion's script command table (opcode, needs-reference flag, parameter list) was read for the OpenOblivion script compiler.

## Oracles for RE claims
Pick the cheapest mechanical check that can prove your next claim wrong:
- **Independent second source**: another caller, a different string, an RTTI base list, a sibling-platform symbol.
- **Round trip** (formats): decode -> encode -> decode equals the original.
- **Trace replay** (logic): feed recorded inputs/state into your reimplementation and compare next-state per variable.
- **Real-data test** (OpenOblivion pattern): run your reimplementation over every record in the real data file and assert structural invariants (e.g. the compiler's statement-level opcode sequence equals the bytecode's for all 7,945 scripts that carry both source and bytecode).
- **Scripted scene + screenshot you look at**; **game log**; **byte-matching build** (decomp).
Rules: automate the loop; stop after ~3 identical failures and change approach; write what the oracle did *not* cover; prove an oracle is live (two captures a second apart must differ while the game animates; a frozen capture API can keep answering confidently).

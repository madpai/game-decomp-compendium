---
name: bethesda-gamebryo-re
description: Reverse-engineering and format knowledge for Bethesda's Gamebryo/Creation games, centred on TES IV Oblivion (and useful for Morrowind, Fallout 3/NV, Skyrim, Fallout 4, Starfield): ESM/ESP record layout, BSA/BA2 archives, the TES4 script bytecode and command table, dialogue/quest/INFO/CTDA rules, voice file naming, Gamebryo/Ni* class map from RTTI, SpeedTree, NIF, load order, tools (xEdit, CK, MO2, esplugin, bsa-rs, OBSE/xNVSE/SKSE) and the OpenOblivion port's verified findings. Use for any Oblivion/OpenMW/OpenOblivion task, parsing plugins or archives, compiling or running TES4 scripts, dialogue or quest behaviour, mapping engine classes, or modding Bethesda games. Includes facts measured on the real Oblivion.esm/Oblivion.exe and where each came from.
---

# Bethesda / Gamebryo reverse engineering

Start every Bethesda task with `python3 ../gamedecomp-library/scripts/hub.py prior-art "<game> <topic>"` (decomp projects, agent field notes, engine playbook). The community already has strong tools for plugins and archives; reverse engineering is needed mostly for *engine behaviour* (scripts, dialogue rules, AI, rendering) that the data files do not spell out.

## What is verified here (measured on a retail Steam Oblivion install)
- `Oblivion.esm`: 390 QUST, 3,817 DIAL, 19,278 INFO, 2,393 SCPT; 48,531 INFO conditions, **all CTDA records are 24 bytes**; condition type byte low bits `0x1` OR, `0x2` run-on-target, `0x4` use-global; operator = `type >> 5` (0 `==`, 1 `!=`, 2 `>`, 3 `>=`, 4 `<`, 5 `<=`). Record and GRUP headers are 20 bytes (Fallout 3 and later: 24).
- `Oblivion.exe` (Steam build, PE timestamp 0x462392c7, fixed base 0x400000, no relocations, MSVC with **full RTTI**): 1,715 vtables / 1,482 classes recoverable in 0.15 s with `re-binary-recon/scripts/rtti_scan.py`, including `TESForm` subclasses, the whole `Ni*` scene graph, Havok, and `SpeedTree*` shader classes. The exe is wrapped by a protection stub (high-entropy `.bind` section holding the entry point); the code/data sections are readable and are what static analysis uses.
- **Voice files** are `sound/voice/oblivion.esm/<race>/<m|f>/<quest>_<topic>_<INFO id as 8 hex digits>_<response number>.mp3`. Confirmed three ways: archive contents (`Oblivion - Voices1/2.bsa`), the `bsa-rs` documentation example, and the executable's own format string `%s_%s_%08X_%u` next to `Data\Sound\Voice` and the type strings `mp3` (game), `wav` (source), `lip` (lip-sync). Lip files exist in the original; the OpenOblivion port does not use them yet.
- The script command table is a data table in the exe: 40-byte records (long name, short name, opcode, needs-reference flag, parameter list); 370 commands, opcodes 0x1000-0x1171; a condition's function number is opcode minus 0x1000. Pivot: string `GetStage` is referenced from data (the table), not code.

## Task map
| Need | Go to |
|---|---|
| Parse ESM/ESP, GRUP/record/subrecord layout, FormIDs, compression, scripts, CTDA, quests, dialogue | `references/tes4-formats.md` |
| Parse or build BSA (v103/104/105) and BA2 | `references/tes4-formats.md` (BSA section) and the `ba2` crate (0BSD) |
| Engine class map, vtable counts, where features live in the exe | `references/engine-classes-and-exe.md` |
| What the OpenOblivion port decided, which rules are verified vs guesses | `references/openoblivion-findings.md` |
| Tools and ecosystem (xEdit, CK, MO2, LOOT, extenders, Rust crates, OpenMW), licences | `references/tools-and-ecosystem.md` |
| Trace a behaviour in the original exe | `re-binary-recon` (string -> function, RTTI anchors) |
| Hook the running game (offline, single player) | `game-hooking-patterns` (OBSE/xNVSE/SKSE route) |

## Working method for engine-behaviour questions
1. Find the data that drives it (record types, fields) and measure it over the whole file (counts, value ranges, rare cases). Assertions over every record beat reading five examples.
2. Find the code that interprets it: string pivot or RTTI class -> function; read the branch structure, not just names.
3. State the rule, its evidence level (documented in the Construction Set wiki / inferred from data / read from exe / observed in game), and what would falsify it.
4. Implement with an oracle: run your reimplementation over all real records and compare an invariant to ground truth (OpenOblivion: compile every script that has both source and bytecode and compare the statement-level opcode sequence: equal for all 7,945; two differ because their source lacks an End/Endif).
5. Record unknowns as guesses in the code and the docs (a table with Status per rule), not as facts.

## Guardrails
Own copy of the game only; never commit game data or tables extracted from the exe (the command table and any exe-derived dump stay private); `esplugin` and `libloadorder` are GPL-3.0 (do not paste their code into non-GPL projects); do not touch DRM or anti-tamper; single-player/offline only for runtime work.

---
kind: game
title: "Oblivion.exe static recon: full RTTI, voice file naming, and game-setting defaults compiled into the exe"
game: "The Elder Scrolls IV: Oblivion"
games_also: []
game_version: "Steam retail build, PE timestamp 0x462392c7 (2007-04-16), Oblivion.esm from the same install, Linux host with Python 3.14"
platform: windows
engine: gamebryo
route: reimplementation
tools: ["re-binary-recon scripts (pe_info, rtti_scan, string_xrefs)", "bethesda-gamebryo-re/gmst_defaults.py", "bsa-rs docs"]
anti_cheat: "None involved: files read from disk only; the exe was never run, attached to or patched (a protection stub wraps the entry point)"
status: working
agents: ["Claude Code (Sonnet 5.5)"]
humans: []
date: 2026-10-06
links: ["https://github.com/madpai/OpenOblivion/blob/main/docs/research/EXECUTABLE_RECON.md"]
tags: [rtti, vtable, gmst, voice-files, static-analysis, openmw, port]
---

# Oblivion.exe static recon: full RTTI, voice file naming, and game-setting defaults compiled into the exe

> Static analysis of the retail Steam executable, in support of an OpenMW-based Android port. It has full MSVC RTTI (1,715 vtables, 1,482 classes), the voice file name format is confirmed by the exe itself, and ~2,050 game-setting defaults live in static initializers (so "settings absent from the master" still have values). All results come from read-only scripts that finish in under a second.

## Setup
Steam `Oblivion.exe` (x86 PE32, image base 0x400000, **no base relocations**, 7.9 MB) plus `Oblivion.esm` and the voice BSAs. Python 3 only; the scripts are `re-binary-recon/scripts/{pe_info,rtti_scan,string_xrefs}.py` and `bethesda-gamebryo-re/scripts/gmst_defaults.py` from this repository. No disassembler needed.

## Route and why
Pure static recon, because the goal was evidence for engine rules the data files do not state (dialogue topic lists, quest-script delay, movement settings), not a rebuild of the exe. A matching decomp would cost far more than the behaviours it would clarify.

## How the game works (what we learned)
- **RTTI is complete.** The TESForm hierarchy (`TESQuest`, `TESTopic`, `TESTopicInfo`, `Script`, `TESObjectREFR` with 105 virtual slots, `Actor`/`Character`/`PlayerCharacter` with 239), the Ni* scene graph, Havok wrappers, `SpeedTree*` shader families, ~38 `*Menu` classes (including barter `NegotiateMenu` and `PersuasionMenu`) and the actor LOD process classes are all named.
- **Voice files**: the base name is built with a `quest_topic_INFOid8hex_responseN` format string next to `Data\Sound\Voice`; the type strings `mp3` (game), `wav` (source) and `lip` (lip-sync) sit in the same string block. Same pattern seen in the archives and in the bsa-rs docs example, so it is verified three ways.
- **Script command table**: 40-byte records referenced from *data*, which is why searching for a command name finds no code references.
- **Game settings (GMST)**: each is created by a static initializer, in one of two instruction orders (see gotcha 4). The master's GMST records override the compiled default; effective value = master record if present, else exe default.
- Condition (CTDA) records are 24 bytes in all 48,531 INFO conditions of the master.

## Build steps
1. `python3 pe_info.py Oblivion.exe` (record the timestamp; note `.bind` high-entropy section).
2. `python3 rtti_scan.py Oblivion.exe > classes.tsv` (keep private).
3. `python3 string_xrefs.py Oblivion.exe --grep 'Voice|%08X'` to find the voice-path assembly.
4. `python3 gmst_defaults.py Oblivion.exe --esm Oblivion.esm --tsv > gmst.tsv` (keep private).

## Verification
Name coverage: the GMST extraction covers 378 of the 382 GMST records in the master. An independent disassembly-based extractor (objdump text, floats only) agreed on all 711 float defaults it produced. Voice naming matches archive contents and the bsa-rs example. CTDA size measured over every condition. **Not verified**: runtime behaviour (the exe was never run), the topic-list rule, the quest-script delay value, struct layouts of the classes.

## Gotchas
1. **Entry point sits in a high-entropy `.bind` section.** **Cause:** a protection stub wraps the exe. **Fix:** analyse only the readable `.text/.rdata/.data`; do not attempt to remove the wrapper; everything above was possible without it.
2. **String has no code references.** **Cause:** it is referenced from a data table (command table, setting table). **Fix:** treat data xrefs as table entries, compute the record stride from consecutive references, and read the table.
3. **Naive GMST scan found only strings.** **Cause:** floats load their default with `fld [addr]; push ecx; fstp [esp]` (an offset arithmetic bug of mine made the scan miss them). **Fix:** anchor on `push NAME; mov ecx, OBJ; call` and look back exactly 10 bytes for the float form, 5 bytes for `push imm32`.
4. **~20% of settings still missing.** **Cause:** 0.0 and 1.0 use `fldz`/`fld1`, and for those the compiler puts `mov ecx, OBJ` *before* `push NAME`; small ints use `push imm8`. **Fix:** scan both instruction orders and both push forms; coverage went from 285 to 306 to 378 of 382.
5. **Most exe defaults differ from the master's values.** **Cause:** the master overrides placeholder defaults (strings like "Need a gamesetting description."). **Fix:** do not use equality with the master as the oracle; use name coverage, an independent extractor, and non-trivial equal values.
6. **`approx func` from the string tool lands mid-function.** **Cause:** it only looks for the previous padding run. **Fix:** treat it as a reading start, confirm with a prologue.
7. **Dumps are exe-derived.** **Fix:** keep class maps and setting tables out of public repositories; publish method, counts and rules.

## Open questions
Read the topic-list construction and quest-delay setting from the code of `TESTopic`/`TopicInfoArray`/`DialogMenu`/`TESQuest`; use `.lip` files for expressions; recover the character body dimensions (not GMSTs).

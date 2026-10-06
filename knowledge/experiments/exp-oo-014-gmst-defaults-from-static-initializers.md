---
id: EXP-OO-014
title: "Recover game-setting defaults from an executable with no symbols by scanning static-initializer patterns"
project: openoblivion
result: worked
level: verified
why_level: verified
scope: build
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5)"]
about: [technique:static-initializer-scan, subsystem:binary-recon, game:oblivion, technique:string-xref-pivot]
games: [game:oblivion]
tags: [gmst, static-initializer, x86, settings, pattern-scan, no-symbols]
related: []
---

# Recover game-setting defaults from an executable with no symbols by scanning static-initializer patterns

## Symptom
About 2,050 game settings exist, but the master overrides only 382; the others (jump, swim, fall, encumbrance, persuasion, barter, disposition) had no known values. The executable has RTTI for classes but no function names, and a string search for a setting name finds the name but no code references.

## Hypothesis
Each setting is created by a static initializer that pushes the name string and loads its default through a recognisable instruction pattern, so a pattern scan anchored on the name push can recover (name, default) without a disassembler.

## Environment
Steam retail Oblivion.exe (x86 PE32), PE timestamp 0x462392c7, read-only; pure Python scanner; `Oblivion.esm` from the same install for name coverage.

## Change
Iterated four times. The first anchored on the name push but its float form had an offset arithmetic bug, so it found only strings. Second, the float form (default loaded just before the pushes) lifted coverage to 285 of 382. Third, `fldz` and `fld1` (0.0 and 1.0), where the object load comes before the name push, gave 306. Fourth, small integers pushed as imm8 and both instruction orders gave 378 of 382.

## Oracle
Name coverage against the master's GMST records (the equality of values is not an oracle, because the master deliberately overrides placeholder defaults); an independent disassembly-text extractor (floats only) that agreed on all 711 float defaults it produced; non-trivial equal values where the master does not override; placeholder strings decoded plainly.

## Result
Worked: 378 of 382 master GMST names covered after four iterations, with the independent cross-check agreeing on every float. The four remaining names (region texture-generation settings) use another initializer form. The exe was never run, so these are static defaults.

## Why
Each setting registers through one of two instruction orders with several push forms; each of the first three iterations missed a form that the compiler uses for a subset of values. Coverage plus an independent extractor, not equality with the master, is what exposed the gaps.

## Next
Effective value is the master's record if present, else the executable default. Keep the output private (an executable-derived table); share the method and counts. Apply the same anchor-and-look-back approach to the command table and to quest or dialogue settings.

## Unverified
Runtime values; that settings never change after initialization; the four ESM-only names; other builds of the executable.

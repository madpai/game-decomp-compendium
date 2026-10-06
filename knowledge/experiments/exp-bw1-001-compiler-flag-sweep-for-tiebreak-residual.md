---
id: EXP-BW1-001
title: "Sweep compiler knobs to fix a matching residual that is an MSVC 6 inliner tie-break"
project: bw1-decomp
result: failed
level: documented
why_level: documented
scope: project
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5), from the BW1 project's AGENTS.md at the cited revision"]
about: [problem:compiler-tiebreak-mismatch, subsystem:matching-decomp, compiler:msvc, game:black-and-white]
games: [game:black-and-white]
tags: [matching-decomp, msvc6, tie-break, inline-budget, fakematch, sweep]
related: []
---

# Sweep compiler knobs to fix a matching residual that is an MSVC 6 inliner tie-break

## Symptom
A function still differs from the target object code after rewrites, and the only remaining difference is the operand order of equal-cost x87 operations inside inlined bodies (or swapped registers).

## Hypothesis
A different compiler flag, build knob or source phrasing produces the target order, and a large sweep over knobs will find it.

## Environment
The Black & White decompilation (MSVC 6 `c2.dll`, dtk and objdiff). Recorded from the project's AGENTS.md at revision be339126394b6fe35699f75b1d300623188b1628 (2026-10-06) and paraphrased; not reproduced here.

## Change
Sweeping build knobs and rewrite variants. The project's text cites a 5,000-build sweep over knobs that never touch the differing instructions as what this costs.

## Oracle
objdiff per-symbol match, and the project's `tiebreak-probe.py --dummies` batch, in which some counts of unused locals match and others do not.

## Result
Failed, as the maintainers record it: a sweep over knobs that never touch the differing instructions finds nothing, and the residual turns out to be a `c2` tie-break.

## Why
The order of equal-cost operands inside inlined bodies depends on how much intermediate code the inliner has built earlier in the same function, not on anything the source means. Reverse-engineering the compiler's tie-break rule has not paid off. (Documented by the BW1 maintainers; not independently checked.)

## Next
Classify the difference before experimenting (real source difference, tie-break or scheduling, inline budget, naming, layout, hand-written asm). Prove that a knob moves the output before sweeping it, bound the search, and when only an equal-cost operand-order residual is left, leave the function non-matching with a TODO or ask the human whether to accept a fakematch.

## Unverified
Not reproduced by this repository; specific to MSVC 6 and BW1's tooling; other compilers' tie-break behaviour not covered.

---
id: EXP-OO-002
title: "Native post-physics camera smoothing for the per-tread stair jolt"
project: openoblivion
result: worked
level: verified
why_level: inferred
scope: project
status: final
date: 2026-10-01
agents: ["Claude Code (Sonnet 5.5), recorded from project docs and private metrics"]
about: [subsystem:camera, engine:openmw, problem:stair-camera-jolt, technique:paired-same-binary-probe, technique:hash-locked-receipts]
games: [game:oblivion]
tags: [stairs, camera, smoothing, native, post-physics, eye-height]
related: [EXP-OO-001]
---

# Native post-physics camera smoothing for the per-tread stair jolt

## Symptom
The same per-tread vertical view jolt as EXP-OO-001, after the Lua `onFrame` filter regressed the real Vilverin ascent.

## Hypothesis
The same bounded smoothing, sampled from the tracked actor root inside the camera position update (after physics and world transforms) and applied before the original focal and camera sphere casts, removes the jolt on both directions without the real-ascent regression, because it consumes the position the camera actually uses.

## Environment
A small audited camera patch (carried as a hash-locked receipt) in an external integration checkout of the OpenMW 0.52 pin. An environment switch enables it only for zero-distance actor-root views. The same integrated binary was run with smoothing on and off, with the same controls driver and start placement, on the generated 20-step fixture and on the real Vilverin entrance stairs, 2026-10-01 (private evidence `native-*-05`). Metric: view vertical-velocity variation.

## Change
The filter reimplemented in C++ at the post-physics point described above. Player position, movement commands, look and the native camera collision tests are unchanged.

## Oracle
Paired same-binary runs (raw versus native) with the walking-response, stopping and jump/landing gates required to pass, plus controls: healthy first-person tracking (the filter must not activate), look, wall, ceiling and ramp fixtures, and a C++ trajectory suite of 3,817 assertions across stair directions, frame cadences, ramp response and transition resets.

## Result
Improved on every route: generated ascent 2347.48 to 528.79 (-77.5%), real Vilverin ascent 1321.40 to 535.69 (-59.5%), real Vilverin descent 2266.39 to 546.82 (-75.9%). Walking ratios stay near 1 (uphill 1.009 raw and 1.016 native, downhill 0.995 and 0.994). The real ascent shows none of the earlier Lua regression. The owner, on build 0.5-native-stairs, describes the stairs as very smooth with a liked subtle stepping: qualitative feedback, not a timed corpus.

## Why
Inferred. This is consistent with the phase explanation in EXP-OO-001 (the correction now follows the solved step), but the Lua and C++ versions differ in more than timing, so the timing effect is not isolated.

## Next
Keep this 0.5 filter as the stair comparison baseline. Re-run the same paired probe after any body, collision or step-constant change (EXP-OO-003, EXP-OO-006) because they change the tread response. Add Android frame-cadence checks and a perceptual comparison.

## Unverified
Perceived comfort (variation is not a comfort score); Android performance and cadence; whether the filter suits first-person with a healthy head bone (it is only enabled for the actor-root fallback camera); that timing is the only difference from EXP-OO-001.

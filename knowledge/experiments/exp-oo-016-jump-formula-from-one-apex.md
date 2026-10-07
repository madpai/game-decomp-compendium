---
id: EXP-OO-016
title: "Infer the original's jump height from one measured apex (wall-clock, one frame time)"
project: openoblivion
result: failed
level: verified
why_level: verified
scope: build
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5)"]
about: [subsystem:player-controller, struct:bhkCharacterController, technique:replay-oracle, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [jump, apex, frame-rate, measurement-trap, ceiling]
related: [EXP-OO-015, EXP-OO-008]
---

# Infer the original's jump height from one measured apex

## Symptom
A recorded standing jump of the original rose 63.9 to 64.4 units, equal to the minimum jump-height setting (64), while the static formula and the player's Acrobatics 5 predict 69. A second trial in the start corridor rose only 32.7.

## Hypothesis
(a) The Acrobatics term contributes almost nothing (the apex is the minimum setting); or (b) the setting values differ from the master's. Either would make the formula "jump height = minimum" and let the port set 64.

## Environment
Same as EXP-OO-015: live sampler at 20 Hz (old capture) and 200 Hz (new), software GL, about 28 updates/s.

## Change
None to the port: this was the reading of one number. The test was to read the controller's own height field, the logged step times and replay the update law.

## Oracle
The controller's jump-height field during a jump; the per-update velocity and step time; a replay of `v -= g dt; z += v dt` over the logged updates.

## Result
The field held 69.0 units (Acrobatics 0.05 in the controller): hypothesis (a) and (b) rejected. The 64.4 apex follows from the same formula integrated with 35 ms steps; at 60 Hz it would be 66.8 and in the continuous limit 69. The 32.7-unit trial was a ceiling: velocity collapsed from 23.3 to 2.1 Havok units/s in one update.

## Why
Verified: frame-time integration (semi-implicit Euler) lowers the realised apex, and the original's apex varies with frame rate. A single apex number cannot identify a formula unless the step is known; a trial under a ceiling is not a jump measurement.

## Next
Measure the controller's own height field and replay with logged step times (technique note "replaying a character controller from its own timesteps"); vary the input (Acrobatics 0, 50, 100) before inferring a formula. Do not set the port's jump from an observed apex.

## Unverified
Frame rates other than the recorded ones; the original at 60 fps on hardware GL.

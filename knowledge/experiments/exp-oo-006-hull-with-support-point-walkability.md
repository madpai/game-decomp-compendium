---
id: EXP-OO-006
title: "Measured hull plus walkability judged from the support point under the hull centre"
project: openoblivion
result: worked
level: verified
why_level: inferred
scope: project
status: final
date: 2026-10-03
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [subsystem:player-controller, struct:bhkCharacterController, engine:openmw, tech:bullet, technique:paired-same-binary-probe, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [player-body, hull, stairs, walkability, support-point, vilverin]
related: [EXP-OO-005, EXP-OO-003, EXP-OO-002]
---

# Measured hull plus walkability judged from the support point under the hull centre

## Symptom
The hull-only build (EXP-OO-005) made the player climb at about 1.4 times the requested distance because the cone's tread-edge contact failed the donor's walkable-normal test.

## Hypothesis
The original's own contact manifold reports a horizontal support plane directly beneath the hull apex while a second, steep contact touches the cone face. Judging walkability from the surface under the hull centre, as the original appears to, should give ramp-like stair motion without the stair hack firing.

## Environment
Same recorded desktop binary for every row, software GL, one async physics worker, the Android player model and settings rewrite, 2026-10-03 (private evidence `tes4-body-final-*`). Metric: `walk_player_vertical_velocity_variation` (lower is smoother) plus the walk, stop and jump gates.

## Change
For the hull only: walkability is judged from the surface directly beneath the hull centre, in the stepper's step-down test and the solver's ground test. Missing support, or support beyond the apex plus the 34-unit step reach, falls back to the contact normal. Step constants 34 and 62, gravity, speeds and the camera filter are unchanged.

## Oracle
Same-binary rows, template box against measured hull. Also the original's own Z(Y) height samples on the Vilverin stairs, a low-ceiling fixture, a ramp, a wall (must block), and the gate closed/open/closed ray hits.

## Result
Worked on desktop. Variation, box then hull: generated ascent 2,127.6 to 1,469.4 (-31%), descent 2,338.5 to 1,547.8 (-34%), Vilverin entrance with authored collision 2,533.9 to 1,448.1 (-43%). Height against the original's samples on the Vilverin stairs (mean, median, RMS): +6.58, +10.0, 8.44 with the box; -0.30, +0.72, 5.23 with the hull. The low-ceiling stair passes (distance ratio 0.97; the box was blocked at 0.24). The ramp rose from 82.6 to 91.1, the wall blocks as designed, and the closed gate stops the body 7.64 units earlier, the radius difference. Peak speeds stay in 163 to 177 for both bodies. Phone acceptance was pending when recorded.

## Why
Inferred. It matches the measured support-under-apex contact in the original, and the cone resting on tread edges is what plausibly makes the original's stairs a ramp rather than discrete steps. The rule is a port choice, not Havok's algorithm.

## Next
Phone acceptance of the hull build for stairs, gate, corridors, low ceilings, jumping and sneaking. Measure the original's stepping (maximum step height, slope limit), gait and jump so the 34/62 constants can be replaced by recovered values.

## Unverified
The original controller's stepping, slope limit, race scaling and acceleration; box-body variation differs between repeated runs (2,379 versus 2,128 on ascent), so only row comparisons are meaningful; the original's stair walk moved at 82 units/s while the probe moves at 150, so the height comparison is approximate.

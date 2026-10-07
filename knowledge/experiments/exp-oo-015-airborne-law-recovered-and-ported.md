---
id: EXP-OO-015
title: "Recover the original's jump, gravity and air-control laws from the running game and port them behind a switch"
project: openoblivion
result: worked
level: verified
why_level: verified
scope: build
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5)"]
about: [subsystem:player-controller, struct:bhkCharacterController, engine:openmw, technique:replay-oracle, technique:runtime-memory-sampler, technique:paired-same-binary-probe, technique:hash-locked-receipts, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [jump, gravity, air-control, integration-order, frame-rate, replay, receipt]
related: [EXP-OO-008, EXP-OO-016, EXP-OO-007]
---

# Recover the original's jump, gravity and air-control laws from the running game and port them behind a switch

## Symptom
The port's jump reached about 113 units on the donor (about 78 on the generated fixtures) with the donor's Morrowind-derived gravity (627 units/s^2), a 0.707 launch factor when moving, and a half-strength air steering. The original felt different, and the project's docs listed jump, gravity and fall as unmeasured.

## Hypothesis
The original's controller is a state machine whose airborne update is a simple per-update law of the game settings. Static reading of the state update functions gives its structure; sampling the live controller at several times its update rate and replaying each candidate law over each logged update will confirm it exactly or reject it.

## Environment
Owner's retail Steam copy (PE timestamp 0x462392c7) run unchanged under Proton on an isolated display with software GL (about 28 updates/s), offline, read-only sampling at 200 Hz, real XTEST input, console `player.setpos` and `setav` for placement and Acrobatics. Port: desktop OpenMW 0.52 pin in the build container, same binary with the switch off and on; the older Android donor tree was compiled with the same receipt. Metrics: apex, fitted gravity, trajectory against the law with a free takeoff time, walk distance ratio, vertical-velocity variation, gates.

## Change
New last receipt `tes4_airborne` (opt-in `OPENOBLIVION_TES4_AIRBORNE=1`): gravity 73.575 Havok units/s^2 (514.95 game units), takeoff `sqrt(2 g h)` with `h = min + (max - min) * Acrobatics / 100` and the horizontal velocity kept, one step of gravity carried in the launch speed because the donor integrates explicitly, and air control `v += f (wanted - v)` per controller update with `f = fJumpMoveBase + fJumpMoveMult * Acrobatics / 100`. Only `character.cpp` and `constants.hpp` change; the solver and body receipts stay untouched.

## Oracle
Replay over every logged airborne update using the update's own `dt` (residual should be zero), first airborne velocity against `sqrt(2 g h) - g dt`, at Acrobatics 5, 50 and 100; then the port's own probe: apex, gravity fit and the paired regression rows (stairs, ramp, wall, low ceiling).

## Result
Replay residual 0.000 in position and velocity on 75, 28 and 18 airborne updates (including a 166 ms frame); first airborne velocity matches to four decimals on three jumps at Acrobatics 5 and at 50 and 100 (height field 9.8585, 16.2879, 23.4318 Havok units = 69, 114, 164). Horizontal gain replays exactly at Acrobatics 5; at 100 it measured 0.28 to 0.29 against 0.3 predicted, on stairs. Port, switch off then on: standing jump rise 78.0 to 66.7 (modelled original at 60 Hz: 66.8), fitted gravity 620.3 to 513.6 (original 514.95); trajectory against the law max 1.8 units, apex 0.08; walk ratio, wall, ceiling, ramp and stair gates unchanged; descent variation +1.5 to +3.4% (settle fall under new gravity); 25/25 CTest; the older donor tree compiles and passes the scripted device checks.

## Why
Verified: every number above is a replay or a paired probe. The reason apexes differ from the formula is the integration: the original steps with the frame time (semi-implicit Euler), so a 35 ms update gives 64.4 units for a formula height of 69 and 60 Hz gives 66.8. The port reproduces the 60 Hz case.

## Next
Read and sample the proxy's support check (the original keeps the ground state through 38-unit drops and captures landings about 15 units early; see finding `oblivion-grounded-state-falls-under-gravity`); step height and slope limit; fall damage; fatigue per jump; swimming; original at 60 fps with hardware GL; phone retest of the feel when the owner resumes.

## Unverified
Phone behaviour; NPC and creature jumps (stand-in values); encumbrance and fatigue; the scripted device checks do not exercise a jump; Acrobatics 100 air control on flat floor; frame rates other than the recorded ~28 Hz; the Java switch inside the app was not independently observed.

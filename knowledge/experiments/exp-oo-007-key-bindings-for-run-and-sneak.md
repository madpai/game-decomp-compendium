---
id: EXP-OO-007
title: "Obtain Oblivion's run and sneak speeds by changing key bindings on the donor engine"
project: openoblivion
result: failed
level: verified
why_level: verified
scope: project
status: final
date: 2026-10-03
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [subsystem:player-controller, engine:openmw, problem:tes4-movement-parity, subsystem:input-ui]
games: [game:oblivion]
tags: [gait, run, sneak, speed, key-bindings, animation-state]
related: [EXP-OO-008]
---

# Obtain Oblivion's run and sneak speeds by changing key bindings on the donor engine

## Symptom
Owner report: sneak did nothing and run felt the same as walk. Oblivion's normal travel mode is run.

## Hypothesis
The gait is a control-binding problem on the borrowed engine: a run toggle, a Caps Lock pulse, or a held Shift with always-run pinned off would switch gait.

## Environment
OpenOblivion phone previews 0.6-run-toggle, 0.7-controls and 0.8-run (a settings pin plus the touch overlay), with phone QA logs; a desktop probe on the same engine. Metric: horizontal speed over grounded moving samples.

## Change
Three successive binding schemes: a run toggle, a Caps Lock pulse, and hold-Shift-for-run with always-run pinned off. Physics, gravity and collision unchanged.

## Oracle
Grounded moving-sample speed from phone logs, and the probe's `current_speed` for requested walk, run and sneak. A working gait shows a second speed band.

## Result
Failed on every build. Build 0.7 stayed at a median of about 151 units/s. Build 0.8 over 357 grounded moving samples across 25.7 simulation seconds had median 149.9, maximum 165.1, nothing above 200. The desktop probe measured walk, run and sneak all at 150 while the engine reported a run speed of 337.5. Builds 0.6 and 0.7 were withdrawn.

## Why
The borrowed engine selects run or sneak speed only while the character animation state machine is in a run or sneak state. The preview player had no TES4 locomotion animations (its template body failed to load), so the state never changed and the player always moved at the Morrowind walk speed. Observed directly by the probe, so the mechanism is verified for this setup.

## Next
Stop experimenting with bindings. Compute ground speed from the original's settings-based formula and override the engine's maximum-speed function directly (EXP-OO-008).

## Unverified
Behaviour once TES4 locomotion animations exist; whether a binding change would work on an actor that does have run and sneak animations.

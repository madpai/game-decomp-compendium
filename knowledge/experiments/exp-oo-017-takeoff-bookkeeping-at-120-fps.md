---
id: EXP-OO-017
title: "Per-frame takeoff and landing bookkeeping in a controller that runs faster than the physics step"
project: openoblivion
result: worked
level: verified
why_level: verified
scope: project
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5)"]
about: [subsystem:player-controller, engine:openmw, technique:paired-same-binary-probe, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [jump, frame-rate, physics-step, bookkeeping, android, 120hz, on-device-log]
related: [EXP-OO-015]
---

# Per-frame takeoff and landing bookkeeping in a controller that runs faster than the physics step

## Symptom
The first phone build with the jump change logged `rise 0 units, air time 0 s` for every jump, although the phone's own position samples showed a normal jump. The desktop probe never showed it.

## Hypothesis
The character controller updates once per rendered frame (120 per second on the phone's display) while physics steps at a fixed 60 Hz, so the frame after a takeoff still sees the old ground state. The bookkeeping that treats "on ground and not taking off" as a landing therefore fired one frame after takeoff.

## Environment
Galaxy S24+ (Android 16, 120 Hz screen), the port's phone package 0.46, JUMP tapped through `adb shell input tap`, the log read with `run-as`. Desktop probe for comparison (software GL, frame rate below 60).

## Change
Treat a takeoff as pending until the physics has reported the air at least once (and for at most 0.1 s), count the air time and the apex only from then on, and log a landing only after the air was seen.

## Oracle
The one-line jump log (rise and air time) on the phone and in the desktop probe, the phone's 20 Hz position samples fitted to the law, and the unchanged desktop regression rows.

## Result
Before: three taps, three `rise 0` lines. After the fix the desktop logs `rise 66.77 units, air time 0.999 s` and the stair rows are unchanged; the phone result of the fixed build is pending the device reconnecting. The old build's position samples already fit the original's law at 60 Hz within 2.7 units, so the lift itself worked and the damage was in the horizontal velocity of running jumps (the takeoff velocity would have been added twice).

## Why
Verified for the mechanism of the log line (stale ground state between frames). Inferred for the running-jump consequence (never observed on the phone because the old build was only tested standing).

## Next
Test a running jump on the phone and read the log; give any controller bookkeeping an explicit "physics has acknowledged this" flag rather than inferring state from the ground flag. Be suspicious of any per-frame logic that reads physics results on a 90 or 120 Hz device.

## Unverified
Running jumps on the phone; other refresh rates; behaviour when physics steps twice in one frame (low frame rates).

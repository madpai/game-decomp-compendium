---
id: EXP-OO-009
title: "Player cannot pass the open Vilverin gate: the failed player collision model, not the gate"
project: openoblivion
result: worked
level: verified
why_level: verified
scope: project
status: final
date: 2026-10-03
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [problem:silent-asset-load-failure, subsystem:collision, engine:openmw, subsystem:player-controller]
games: [game:oblivion]
tags: [doorway, error-marker, osgt, asset-load, diagnosis, gate]
related: [EXP-OO-003]
---

# Player cannot pass the open Vilverin gate: the failed player collision model, not the gate

## Symptom
Owner report on build 0.18-audio: both hall-gate leaves visibly open, but movement attempts after Open stop at the doorway. The log shows successful Open/Close/Open playback and then `Unmatched property only., expecting UniqueID`, `Unsupported wrapper class Collision` and `Failed to load 'meshes/basicplayer.osgt'`.

## Hypothesis
The symptom pointed at the door (leaves open, body stops at the doorway), so the animated leaf boxes or the frame were suspected. The diagnosis that held: the player collision model failed to load, the engine substituted its embedded error-marker body, and that body is wider than the opening.

## Environment
OpenOblivion 0.18 on the OpenMW pins; OSG 3.6.5 ASCII reader; desktop probes with double-precision Bullet and one async physics worker; an independently written private JNI harness linking the unchanged ARM64 OSG static libraries on an isolated Android 14 emulator (model decoding only, no GL scene). Marker width about 123.2 units, frame opening about 111 units at mid height and 126.75 at the floor, the intended template body 26.6 units wide.

## Change
Two defects removed from the OSGT file: it had one Generator value where OSG's ASCII stream reads two, and extra `#` prose lines after the header that OSG does not skip. Geometry, collision node name, settings rewrite and body dimensions unchanged.

## Oracle
The preserved old file reproduces the exact parser errors with OSG 3.6.5. A new CTest fixture uses the real OSG reader and checks the hierarchy, eight vertices, twelve triangles and all six bounds. Native Vilverin before/after probes with the same gate and frame: old file, the player stays at local Y -13.6 after Open; corrected file, blocked at Y -18.28 while closed and crossing to Y +373.57 after Open. The ARM64 harness reports old file rejected and fixed file passing.

## Result
Worked on desktop and in the emulator harness; the physical phone passage retest was pending. A model that fails to load now fails the probe independently of visual gate success.

## Why
The engine silently substitutes an embedded error marker for a model that fails to load; the 123-unit marker cannot pass a 111-unit opening, which looks exactly like a collision defect. The earlier desktop gate probes used a healthy DAE model, so nothing had exercised the Android OSGT load path.

## Next
When movement is blocked, read the log for model or asset load errors before debugging collision geometry, and measure the body that is actually in use. Make a failing supplied asset fail the test run, not just log.

## Unverified
Physical-phone passage; whether other silent substitutions exist for other asset kinds.

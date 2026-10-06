---
id: EXP-OO-005
title: "Swap in the measured pointed player hull without changing the donor's ground solver"
project: openoblivion
result: failed
level: verified
why_level: inferred
scope: project
status: final
date: 2026-10-03
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [subsystem:player-controller, struct:bhkCharacterController, engine:openmw, tech:bullet, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [player-body, hull, stairs, solver, stair-hack, step-down]
related: [EXP-OO-006]
---

# Swap in the measured pointed player hull without changing the donor's ground solver

## Symptom
After the original controller's hull was measured (an eight-sided prism with pointed cones at both ends, radius 20.25, height 128), the first port build used that hull as the player body and left the host solver alone. On the original 20-step stair fixture the player climbed far faster than the requested walking speed.

## Hypothesis
Replacing the template box with the measured hull is enough to approach the original's stair contact, because shape was the known difference.

## Environment
OpenOblivion body receipt (`OPENOBLIVION_ORIGINAL_BODY=1`) applied to the donor's actor, stepper and movement solver in the desktop OpenMW 0.52 pin; original generated stair fixture; software GL, one async physics worker; run 2026-10-03 (private development runs `tes4-body-stairs-hull-01/02`).

## Change
Player collision shape replaced by the measured hull with its convex radius as the Bullet margin. Solver, step constants (34 up, 62 down), gravity, speeds and the camera filter unchanged.

## Oracle
Distance ratio (distance travelled over requested distance) and vertical speed on the stair fixture; a healthy run is near 1.

## Result
Failed: the player climbed at 440 to 480 units/s, a distance ratio of 1.42, instead of walking speed. This was a rejected development build, never shipped.

## Why
Inferred. A cone's contact with a tread edge is steeper than the walkable limit, so the solver's normal step-down test fails and the inherited Morrowind "extra stair hack" then moves the body 10 units per frame. The fix in EXP-OO-006, which removes the effect by changing only how walkability is judged, supports this explanation but does not isolate it.

## Next
Judge walkability for the hull from the support point beneath its centre instead of the contact normal (EXP-OO-006). General lesson: when porting a character shape, port the ground-test semantics with it. A pointed shape resting on tread edges is walkable by support point, not by contact normal.

## Unverified
The original controller's own stepping and slope rules; whether the stair hack alone accounts for the whole speed-up; behaviour on other staircases.

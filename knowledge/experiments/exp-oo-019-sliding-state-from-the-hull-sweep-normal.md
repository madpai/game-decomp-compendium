---
id: EXP-OO-019
title: "Reproduce the original's stair free fall by classing the downward hull sweep's contact normal as sliding"
project: openoblivion
result: failed
level: verified
why_level: inferred
scope: project
status: final
date: 2026-10-08
agents: ["Claude Code (Sonnet 5.5)"]
about: [subsystem:player-controller, struct:bhkCharacterController, engine:openmw, technique:paired-same-binary-probe, problem:stair-camera-jolt]
games: [game:oblivion]
tags: [stairs, sliding, contact-normal, cone-hull, support-check]
related: [EXP-OO-018, EXP-OO-005, EXP-OO-006]
---

# Reproduce the original's stair free fall by classing the downward hull sweep's contact normal as sliding

## Symptom
The original keeps the ground state through a stair flight while the vertical velocity accumulates (a free fall per tread), but resets it every update on level ground. The state flags and the proxy's own velocity do not separate the two cases.

## Hypothesis
The support check classifies the surface it finds as supported or sliding (as Havok's character proxy does); the 40-unit-wide cone hull touches a stair nosing with its slanted surface (about 58 degrees, steeper than the walkable limit), so the contact is sliding and the velocity accumulates; on level ground the apex touches a flat surface.

## Environment
The port's desktop probe walking down the real Vilverin stairs from the start of the original's recorded trace, with the grounded law on (mode 1: walkable contacts only; mode 2: plus sliding on the sweep's steep normal).

## Change
After the host solver, sweep the hull down from its height, take the hit normal, and for a steep normal keep the ground state while accumulating `vz -= g*dt`, stopping on contact.

## Oracle
Height against distance along the flight from the original's trace (landing plateaus at 297.7 and 258.3 units) and the ground/air state.

## Result
Mode 1 (steep contacts keep the host's handling) matches the stairs without the receipt. Mode 2 left the hull up to 22 units above the treads and in the air for stretches (original: grounded all the way, within a few units of the treads); the grounded fraction on the generated descent fixture fell from 1.0 to 0.5.

## Why
Inferred: the hull sweep's normal at the top edge of a flight is that of the landing (the hull is still half over it), so the first steps after the edge are classified level and hover; the sweep cannot tell an edge contact from a level contact when the hull straddles an edge. The proxy's real classification is not read.

## Next
Read the proxy's contact and surface-info code (the support check) in the executable and port its rule, then compare the height profile along the flight against the recorded trace again.

## Unverified
That the original's classification is a normal-based one at all; which normal (contact manifold, support cast or centre ray) it uses.

---
id: EXP-OO-004
title: "Apply the Havok vertex scale factor of 7 to bhkNiTriStripsShape vertices"
project: openoblivion
result: failed
level: verified
why_level: verified
scope: build
status: final
date: 2026-10-01
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [struct:bhkNiTriStripsShape, struct:bhkPackedNiTriStripsShape, struct:bhkBoxShape, tech:havok, subsystem:collision]
games: [game:oblivion]
tags: [havok, scale, units, tristrips, niftools]
related: [EXP-OO-003]
---

# Apply the Havok vertex scale factor of 7 to bhkNiTriStripsShape vertices

## Symptom
The collision unit scale of the stair meshes was unknown. Open-source NIF tooling documents a factor of 7 for packed Havok vertices, so strip-shape vertices were expected to need it too.

## Hypothesis
Collision vertices of these NIFs are stored in Havok units and must be multiplied by 7 to reach game units, as for packed shapes.

## Environment
The six Vilverin stair NIFs, OpenMW 0.52 reader. Collision AABB compared with the visible-mesh AABB per axis.

## Change
Multiply the `bhkNiTriStripsShape` vertices by 7 before building the collision mesh.

## Oracle
Per-axis bounds: the collision of a stair should have about the extents of its visible mesh; a wrong scale shows as a constant ratio.

## Result
Failed: with the factor the collision came out about seven times too large. Unscaled, the bounds match the visible mesh on every axis for four of the six meshes (the U-turn and pit meshes differ by a few percent because their collision mesh is simply not the render mesh). The MOPP scale is 1 and the strip shape scale is (1, 1, 1, 0).

## Why
The vertices of `bhkNiTriStripsShape` live in the referenced `NiTriStripsData`, already in mesh units. The factor belongs to the packed Havok vertex layout and to native primitives (box half-extents did need it: on the hall gate, half-extents times 7 reproduce the visible slabs). The scale depends on the shape class, not on the file or the game.

## Next
Choose the scale per shape class: strips times 1 (check the scale fields), box half-extents times 7 (verified on the gate), packed strips times 7 only after measuring one real mesh, convex vertices and capsules unmeasured. Never apply a scale because "Havok data is scaled"; compare bounds first.

## Unverified
Packed strip shapes (zero blocks in this slice), convex vertices and capsule shapes, other games and builds.

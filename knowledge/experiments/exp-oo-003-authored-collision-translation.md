---
id: EXP-OO-003
title: "Translate authored Havok strip collision (MOPP over tri-strips) into the donor's Bullet world"
project: openoblivion
result: partial
level: verified
why_level: inferred
scope: build
status: final
date: 2026-10-01
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [subsystem:collision, struct:bhkMoppBvTreeShape, struct:bhkNiTriStripsShape, struct:bhkRigidBody, tech:bullet, engine:openmw, technique:authored-collision-translation, problem:tes4-collision-fidelity]
games: [game:oblivion]
tags: [collision, havok, mopp, tristrips, bullet, stairs, authored-collision]
related: [EXP-OO-004, EXP-OO-006]
---

# Translate authored Havok strip collision into the donor's Bullet world

## Symptom
The donor engine builds Oblivion collision from the visible render geometry and ignores the authored Havok blocks. Stairs may therefore snag differently from the original, and speed tuning was blocked. The working suspicion (an inference, not a measurement) was that the render mesh is denser than the Havok mesh and has no stair layer.

## Hypothesis
Importing the triangles of the authored `bhkMoppBvTreeShape` over `bhkNiTriStripsShape` for fixed `OL_STATIC` bodies gives a surface closer to the original's, without executing MOPP or shipping Havok's cooker.

## Environment
Six stair NIFs of the owner's Vilverin visual slice (version 20.0.0.4, user version 10 or 11). Loader behind `OPENOBLIVION_AUTHORED_COLLISION=1`, built into the desktop OpenMW 0.52 pin (double-precision Bullet, in a container) and compiled for the Android 0.51 base. Accepted bodies: root `bhkCollisionObject`, fixed and quality-fixed, layer `OL_STATIC` on both the world and body filters, MOPP over strips or strips directly, strip and MOPP scale 1, identity root transform; everything else keeps the render-mesh fallback.

## Change
A bounded static loader: triangles built in stored units and added as one compound child at the origin, the rigid-body translation not applied, MOPP bytes unused, degenerate strip steps omitted the way the render path omits them. The player body, the 34/62 step constants and the camera filter were unchanged.

## Oracle
Bullet triangle counts and AABBs with the switch on and off for each mesh, and a 20 by 20 downward ray grid on each shape's AABB, paired where the AABBs match. A character-controller stair trace was not part of this experiment.

## Result
The loader works and the surfaces differ. Bullet triangle counts, authored versus render: 213 and 866, 165 and 700, 1,522 and 4,632, 575 and 1,486, 751 and 2,066, 268 and 756 across the six meshes. AABBs match on four of six. On `arwhallstairs01` 245 rays hit both shapes with a median absolute height difference of 2.32 units (188 rays differ by more than 1, 19 by more than 16, maximum 372.7); the bridge median is 2.44, `arnhallstairs01` 0.55, the entrance and pit 0. No movement trace and no owner report on the 0.9 package (which carries the switch) existed when this was recorded, so the effect on stair feel is unknown. The owner's liked 0.5 feel was camera smoothing on top of the render-mesh surface.

## Why
Partial because a surface comparison is not a movement comparison. The body was still the template box with Morrowind step constants, so any movement difference could not be attributed to the collision surface. That authored collision has about half the render triangles is measured; that this explains tread snags is inferred.

## Next
Repeat the stair traces with the measured player hull on both surfaces (EXP-OO-006), and collect the owner's 0.9 stair report. Extend the loader to packed strip shapes only when a mesh outside this slice needs them.

## Unverified
Any effect on character movement; non-fixed bodies (keyframed doors, clutter); other meshes, other games and the Fallout 3 or Skyrim block variants; equivalence of MOPP-culled Havok queries with the full triangle set.

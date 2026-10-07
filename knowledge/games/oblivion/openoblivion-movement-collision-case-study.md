---
kind: game
title: "OpenOblivion movement and collision case study: authored Havok collision, the measured player hull, stair camera timing, gait, silent model failures"
game: "The Elder Scrolls IV: Oblivion"
games_also: []
game_version: "Steam retail Oblivion (exe PE timestamp 0x462392c7 for class facts); owner's Vilverin visual slice for data facts; OpenOblivion preview builds 0.3-0.23 on OpenMW 0.52 (desktop pin) and the Android 0.51 base"
platform: windows
engine: gamebryo
route: reimplementation
tools: ["OpenMW (patched)", "Bullet", "desktop probe with a scripted controls driver", "read-only process-memory sampler on the owner's own copy", "niftools nif.xml", "PyFFI cross-check"]
anti_cheat: "None involved: owner's own single-player copy, offline; the sampler only read memory of an unchanged copy; nothing written to the process; no DRM or protection touched"
status: in-progress
agents: ["Claude Code (Sonnet 5.5), compiled from the OpenOblivion project docs and private metrics"]
humans: []
date: 2026-10-06
links: ["https://github.com/madpai/OpenOblivion/blob/main/docs/research/HAVOK_COLLISION.md", "https://github.com/madpai/OpenOblivion/blob/main/docs/PLAYER_MOVEMENT.md", "https://github.com/madpai/OpenOblivion/blob/main/docs/research/TES4_PLAYER_BODY.md"]
tags: [havok, bhk, mopp, tristrips, collision, stairs, camera, character-controller, hull, gait, openmw, bullet, android]
---

# OpenOblivion movement and collision case study

> What a patched-donor port learned about Oblivion's Havok-facing movement: collision is authored (and differs from the render mesh), the player is a pointed convex hull and not a capsule, the donor's stair solver breaks when you give it that hull unless you port the support-point ground test, stair camera smoothing must run after physics, and a failed model load can masquerade as a collision bug. Each lesson links an experiment record; reusable physics knowledge is in `bethesda-gamebryo-re/references/{havok-gamebryo-collision,character-controller-and-stairs,physics-backend-translation}.md`.

## Setup
OpenOblivion runs Oblivion data on a patched OpenMW (Bullet physics, own movement solver). Native changes are hash-locked receipts; a desktop probe drives the real player controls through scripted routes (a generated 20-step stair fixture and the real Vilverin entrance stairs) and records trajectory and view metrics; phone and emulator checks are separate. Owner-supplied data stays private; only counts, rules and metrics are public.

## Route and why
Measure before tuning. First the data (NIF census of collision blocks, then the six stair bodies decoded), then the original's controller (read-only sampling of the owner's own running copy), then port semantics in small receipts, each judged by a paired same-binary probe. Experiments, successes and failures alike: `EXP-OO-001` to `EXP-OO-014`.

## How the game works (rules and their status)
- Collision is authored: `bhkCollisionObject` -> `bhkRigidBody` -> `bhkMoppBvTreeShape` -> `bhkNiTriStripsShape` for static stairs, with about half the render triangles and a different surface [verified, slice only].
- Strip vertices are in mesh units; Havok-native boxes need x7; the Havok-space scale is about 1/7 [verified].
- The six stairs are layer 1 fixed stone bodies, not the stairs layer [verified, slice only]; the layer filter matrix is unrecovered.
- The player controller is an 18-vertex pointed convex hull, 20.25 radius, 128 tall, convex radius 0.70, unchanged in all states [verified, one session]; its step height, slope limit, jump and acceleration are not measured.
- Ground speed comes from settings, not animation state [static]; the donor picks gait from animation state [verified].
- The donor's actor constants (34, 62, 46 degrees) are Morrowind's [static, project-scoped].
- **Airborne motor (2026-10-06):** gravity 73.575 Havok units/s^2, per-frame semi-implicit integration (apex depends on frame rate), jump `min + (max - min) x Acrobatics / 100` launched at `sqrt(2 g h)` with momentum kept, and a weak per-update air steering `0 + 0.3 x Acrobatics / 100`, all verified by replaying the running original; the port applies them behind `OPENOBLIVION_TES4_AIRBORNE=1` (EXP-OO-015). The ground state keeps adding gravity (stairs are a free fall per tread) and captures landings about 15 units early; not ported. See `techniques/replaying-a-character-controller-from-its-own-timesteps.md`.

## Verification
Paired same-binary probes (raw versus changed), gates for walking response, stopping, jump/landing, a wall that must block, healthy-tracking control; ray grids on matching AABBs; the original's own Z(Y) samples; independent decoders for animation; emulator before/after harnesses. **Not verified:** any phone result of the hull, authored-collision or gait builds (phone testing is paused), original step/slope/jump, run speed, anything outside the Vilverin slice, and the isolated cause of the Lua-filter regression.

## Gotchas
1. **Per-tread camera jolt although the body climbs fine.** **Cause:** the view follows the player root through discrete rises; an eye filter in Lua `onFrame` runs before physics and the camera update at the OpenMW pin and regressed the real ascent (1206.7 to 3008.3) while passing on the synthetic fixture. **Fix:** apply the smoothing inside the camera position update after physics (1321.4 to 535.7). The phase explanation is inferred, not isolated (EXP-OO-001, EXP-OO-002).
2. **A change looked good on the generated stair fixture and bad on the real stairs.** **Cause:** not established; the synthetic route is a clean staircase and the real treads are irregular, and the Lua filter's result differed even between real ascent (worse) and real descent (better). **Fix:** require a real-stair route in every paired probe and keep the fixture as a first oracle only (EXP-OO-001).
3. **Collision came out seven times too large.** **Cause:** the packed-vertex factor of 7 was applied to `bhkNiTriStripsShape` vertices that are already in mesh units. **Fix:** choose the scale per shape class and compare bounds first (EXP-OO-004).
4. **Player climbed at 440 to 480 units/s after swapping in the measured hull.** **Cause:** the cone's contact on a tread edge failed the donor's walkable-normal test, so the inherited stair hack moved the body 10 units per frame. **Fix:** judge walkability from the support point under the hull centre (EXP-OO-005, EXP-OO-006).
5. **Player stopped at a visibly open doorway.** **Cause:** the player collision model failed to load and the engine silently substituted a 123-unit error-marker body (the frame opens 111 units at mid height). **Fix:** correct the model file and make a failed supplied model fail the probe; read load errors before debugging collision (EXP-OO-009).
6. **Run looked the same as walk; three binding experiments changed nothing.** **Cause:** the donor selects gait from the animation state machine and the preview player had no locomotion animations. **Fix:** override the maximum-speed function with the settings-based formula (EXP-OO-007, EXP-OO-008).
7. **The port stood about 3.25 units higher than the original on flat floor.** **Cause:** the original hull floats about 4 units above the floor triangles and its reference sits below them; the port rested the hull on the floor. **Fix:** not applied; recorded as measured but unreproduced (finding `oblivion-controller-floats-above-floor`).
8. **Triangle counts disagree between the file and the loader.** **Cause:** a serialized strip of length n is n-2 triangles, but degenerate strip steps (two equal indices) are dropped (1,288 serialized, 575 kept on one stair). **Fix:** count the way the loader builds, and say which you mean.
9. **Skeleton loaded, animation clock ran, still a T-pose.** **Cause:** the attachment filter copied each part's private skeleton, so skinned parts bound to bones that were not animated; separately the donor looked bones up by Morrowind names that Oblivion's skeleton lacks. **Fix:** copy the renderable's local subtree so parts resolve the actor's animated bones; list the skeleton's node names before assuming a mapping (EXP-OO-012).
10. **The same configuration gave different numbers in different runs.** **Cause:** run-to-run variation in the probe (box-body ascent variation 2,379 versus 2,128; the real-ascent raw baseline 1206.7 in one series and 1321.4 in another). **Fix:** compare rows produced by the same binary in the same series, change one thing per experiment, and record the metric's name with every number.

## Open questions
Original maximum step height and slope limit; run and sneak speeds in the original; jump impulse and race scaling of the hull; the Havok layer filter matrix; terrain height-field collision; packed-strip prevalence outside this slice; whether the support-point rule matches the original's proxy beyond stairs; phone feel of the hull and authored-collision builds.

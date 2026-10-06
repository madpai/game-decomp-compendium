# Character controllers, stairs and movement: what is known, and how to test it

The player body is where Havok-facing semantics bite hardest: shape, ground test, step handling, speed. This file separates what was **measured in the original** from what a **donor engine (OpenMW at the OpenOblivion pins) does**, then lists symptom-first checks and oracles. Evidence tags: **[static]** read from exe/source, **[verified]** measured with an oracle, **[documented]** upstream statement not re-checked, **[inferred]**, **[guessed]**. Project-scoped results describe one project's choice and are never engine facts. Companion files: `havok-gamebryo-collision.md`, `physics-backend-translation.md`.

## What the original does (Oblivion, retail Steam build)
- The executable names a Havok **character-proxy controller family**: `bhkCharacterController`, `bhkCharacterProxy`, `bhkCharControllerShape`, a point collector, and states `OnGround`, `InAir`, `Jumping`, `Swimming`, `Flying`, `Projectile` [static]. How states are driven is unread.
- The live controller shape is an **18-vertex convex hull, not a capsule**: an eight-sided prism (ring radius 20.25 units) with a pointed cone at each end, 128 units tall, convex radius 0.70, identical while standing, walking, jumping and sneaking (sneak does not shrink it), rotating with heading, hull centre 71 units above the reference position [verified: read-only 20 Hz sampling of the owner's running copy, offline, one session; the diagonal vertices agree with the exe's own cos 45 rounding].
- On flat floor the controller reports a horizontal support contact directly beneath the apex at a distance of 3.3 to 3.4 units; on a stair edge a second, steep contact touches the cone face while the flat support stays under the apex [verified]. The lowest hull point therefore floats about 4 units above the floor triangles and the reference position sits about 2.25 units below them [inferred: assumes the contact is the floor's outer surface including its convex radius].
- A pointed hull resting on tread edges, with support judged under the apex, plausibly makes the original's stair motion a ramp rather than discrete steps [inferred].
- Ground speed comes from **game settings**, not from animation state: walk min/max blended by the Speed attribute, an encumbrance term, no-weapon and sneak multipliers, run = walk times (run multiplier + athletics term) [static]. One walking sample of the original (peak 117.3 units/s on stairs) is consistent with the formula's sheathed walk (116.6); run was never sampled [verified for walk only]. Settings missing from the master still have values compiled into the exe (static-initializer scan, EXP-OO-014) [verified].
- **Not measured:** maximum step height, slope limit, acceleration, jump impulse, swimming, how race height scale changes the hull, the proxy's own step rules.

## What the donor engine does (OpenMW 0.52 pin; project-scoped)
- Actor = Bullet cylinder or box from rendered bounds (default shape a box), step-up 34, step-down 62, maximum slope 46 degrees: Morrowind-era constants, not Oblivion records; its own movement solver and stepper, with extra stair hacks for bad Morrowind assets; no `btKinematicCharacterController` in `mwphysics` [static].
- Run and sneak speed are chosen only while the animation state machine is in a run or sneak state; with no TES4 locomotion animations the player always moves at 150 units/s [verified, EXP-OO-007].
- Collision is generated from visible geometry unless a patch imports authored strips (`havok-gamebryo-collision.md`).

## Stairs: what the OpenOblivion case study showed
1. **Per-tread view jolt with sound physical traversal.** The body climbed fine; the view bounced on every tread. Treat camera and body as separate problems. A Lua `onFrame` eye filter that passed on the synthetic stair fixture **regressed the real Vilverin ascent** (1206.7 to 3008.3); the same idea inside the camera update after physics cut it to 535.7. Lua `onFrame` runs before physics and the camera update at that pin; phase is the best-fitting cause, not an isolated one (EXP-OO-001, EXP-OO-002) [verified result, inferred cause].
2. **Authored collision differs from the render mesh** in triangles and surface height; its effect on a character trace was not recorded (EXP-OO-003) [verified difference].
3. **Port the ground test with the shape.** Swapping in the measured pointed hull alone made the donor's stair hack fire (440 to 480 units/s, ratio 1.42); judging walkability from the support point under the hull centre fixed it and cut view variation 31 to 43% against the template box (EXP-OO-005, EXP-OO-006) [verified; mechanism inferred]. The rule is a port choice, not Havok's algorithm.
4. **Synthetic fixtures are necessary and insufficient.** A generated stair of twenty 16-unit rises and 24-unit treads is a good first oracle; irregular real stairs exposed what it hid.

## Symptom -> first checks
| Symptom | Check first | Record |
|---|---|---|
| Player stops at a doorway that is visibly open | read the log for model or asset load errors; measure the body that is really in use (a failed model is replaced by a 123-unit error marker) | EXP-OO-009 |
| Climbs stairs far too fast after changing the body shape | the solver's step-down/walkable test with the new shape; the inherited stair hack | EXP-OO-005 |
| Camera bounces per tread, body is fine | camera filtering and where in the frame it runs relative to physics | EXP-OO-001/002 |
| Snags on treads | collision source (render mesh vs authored), triangle density, layer filter, then body shape | EXP-OO-003 |
| Run feels like walk, sneak does nothing | how the engine picks gait (animation state) before touching key bindings | EXP-OO-007/008 |
| Walks through walls or stands on invisible things | the layer filter (pick, trigger and non-collidable shapes must not be solid); root transform; shape scale | havok-gamebryo-collision.md |
| Collision seven times too big | per-shape-class scale (strips x1, box half-extents x7) | EXP-OO-004 |
| Stands about 3 units higher than the original on flat floor | the original hull floats above the floor; margin/convex radius | finding `oblivion-controller-floats-above-floor` |
| Blocked in low-ceiling stairs only | box versus hull height; the template box blocked a low-ceiling stair that the measured hull passes | EXP-OO-006 |

## Oracles and fixtures that worked
Scripted controls driver with the same binary for raw and changed runs (no per-frame teleporting); initial placement only to select a surface. Metrics with authored thresholds: distance over requested distance, time below 25% of requested speed, vertical range, grounded fraction, stopping drift, jump and landing, plus view vertical-velocity variation and height against the original's own Z(Y) samples on the same stairs. A large discontinuity invalidates a run (no respawn counted as traversal). Compare rows, not single digits: repeated box-body runs varied (2,379 vs 2,128). The original's stair walk moved at 82 units/s while the probe moves at 150, so height comparisons are approximate. Controls: wall must block, healthy first-person tracking must not activate the fallback camera, a gate closed/open/closed.

## Measuring the original (owner's own copy only)
Offline, single-player, unchanged copy, read-only sampling of the process (`technique:runtime-memory-sampler`): player reference, controller, phantom and shape at a fixed rate across standing, walking, jumping, sneaking, turning and three resting points; use the original's own scale constant to convert. Never write to the process, never touch protected online clients; publish the findings and method, not raw captures or disassembly.

## Next measurements (highest value)
Maximum step height and slope limit; run and sneak speeds in the original; jump impulse; hull scaling by race height; the proxy's behaviour in `InAir`, `Jumping` and `Swimming`; a character-controller trace on authored versus render stairs with the measured hull.

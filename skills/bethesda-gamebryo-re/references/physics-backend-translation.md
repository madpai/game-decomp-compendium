# Translating Havok-facing semantics to an open backend (Bullet and similar)

Goal: keep the **gameplay-visible semantics** of the original's physics and drop everything that is Havok implementation. This is not a plan to reproduce Havok. Evidence tags: **[verified]**, **[static]**, **[documented]** (upstream statement not re-read), **[inferred]**, **[guessed]**. Companion files: `havok-gamebryo-collision.md` (what the data and exe contain) and `character-controller-and-stairs.md` (player body, stairs, symptoms).

## Preserve semantically, or treat as implementation detail?
| Aspect | Verdict | Why / evidence |
|---|---|---|
| Static surface geometry (triangles, units, transforms) | **Preserve** | authored collision differs from render geometry in triangles and height [verified, EXP-OO-003]; scale is per shape class [verified, EXP-OO-004] |
| Which things block the player, camera rays, projectiles, AI rays (layer semantics) | **Preserve** the meaning, not Havok's filter encoding | layer byte is in the body's filter [documented]; the pair matrix lives in Havok's filter and was not recovered [open]; map to group/mask bits and log unknown layers |
| Fixed / keyframed / dynamic motion | **Preserve** as static / kinematic / dynamic | stairs fixed, door leaves keyframed boxes on layer 2 [verified] |
| Triggers and phantoms | **Preserve** overlap events (enter, leave); drop push-out | `bhkSPCollisionObject` carries trigger volumes [documented] |
| Player body shape and ground-test semantics | **Preserve** shape; port the support-point walkability with it | hull measured [verified]; hull alone broke stairs, support-point rule fixed it [verified, EXP-OO-005/006] |
| Step height, slope limit, jump impulse, gait, speed | **Preserve behaviour, but only from measurement or settings** | donor constants are Morrowind's [static]; speed comes from settings [static]; step/slope/jump unmeasured [open] |
| Friction and restitution values, materials with gameplay effect (sounds) | Preserve where gameplay can see it | stairs read friction 0.3, restitution 0.3 [verified]; material-to-sound mapping not studied |
| Ragdolls and constraints | Preserve limits and axes only if ragdoll fidelity matters; otherwise defer | blend collision object and a constraint family exist [static] |
| MOPP bytes and cooker, `hkp*` API, broadphase, solver internals, memory and serialization | **Implementation detail**, do not reproduce | MOPP is an acceleration structure [documented, inferred for import equivalence] |
| Havok world step rate, solver iterations, exact numerics | Not preserved; compare statistically with probes | affects feel, unmeasured [open] |

## Mapping to Bullet (standard Bullet API; [documented], names to check against your version)
- Static triangle strips -> `btBvhTriangleMeshShape` (static bodies only); transform with a `btCompoundShape` child; build from the child shape of MOPP, skip degenerate strip steps (a serialized strip of length n is n-2 triangles, fewer once degenerate steps are dropped: 1,288 serialized vs 575 kept on one stair) [verified count rule].
- Convex hull -> `btConvexHullShape`; box -> `btBoxShape` (half-extents, x7 for Havok-native boxes [verified on the gate]); capsule -> `btCapsuleShape`; list shape -> `btCompoundShape`. Havok's *convex radius* corresponds to Bullet's collision *margin*; the measured player hull uses 0.70 [verified usage in the port].
- Layers -> `collisionFilterGroup` / `collisionFilterMask` bits per body; one table in your code, with an explicit "unknown layer -> not solid, log once" rule.
- Triggers -> a ghost object (`btGhostObject` / `btPairCachingGhostObject`) with no contact response.
- Character -> your own sweep-based solver or `btKinematicCharacterController` (capsule-oriented, step height and slope parameters). OpenMW at the pin uses its own movement solver and stepper, not Bullet's controller [static]. Whatever you choose, make it consume the **measured shape** and a **support-point ground test**.
- Constraints -> by meaning: ball-and-socket -> point-to-point, hinge and limited hinge -> hinge with limits, ragdoll -> cone-twist, prismatic -> slider, stiff spring -> spring on a generic 6-DOF [inferred from names; not validated against Oblivion data].
- Units: pick Bullet world units = game units (OpenMW does) and convert Havok-space values by about x7 [verified for Oblivion hull and boxes]. Build Bullet in double precision if the host does (the OpenOblivion container build is `BT_USE_DOUBLE_PRECISION`) [verified for that image].

## Workflow
1. **Census** collision blocks in the user's data (block types, layers, motion, quality, scale fields) and pick the smallest useful subset; fixed static bodies first.
2. **Translate** with a bounded loader that accepts only what it understands (root transform, scales, layer, motion) and falls back to render geometry with a log line; never silently widen.
3. **Compare surfaces** with a ray grid on matching AABBs, then **compare movement** with a paired same-binary probe on real stairs, not only a synthetic fixture.
4. **Measure the original controller** (owner's own copy, offline, read-only) and port shape, ground test and constants from measurement; do not mix two unmeasured changes in one experiment (applying published speed defaults on top of render-mesh collision would confound speed and surface).
5. **Record** each attempt as an experiment (`hub.py template experiment`) with result level and why level; run `hub.py tried` before repeating an idea.

## Do not
Reproduce Havok or ship its tools; execute MOPP; apply a vertex scale to a class you have not measured; trust a synthetic fixture alone; borrow another engine's step height or slope as if it were the original's; turn one project's choice (a support-point rule, a 100 ms camera filter) into an engine fact; use runtime sampling on anything but your own offline single-player copy.

## Open questions
The layer filter matrix; step height and slope limit of the original controller; terrain height-field collision; whether MOPP-culled queries equal full-mesh queries; packed-strip handling for Fallout 3 and later [guessed relevant; census first]; collision material effects on sounds and friction.

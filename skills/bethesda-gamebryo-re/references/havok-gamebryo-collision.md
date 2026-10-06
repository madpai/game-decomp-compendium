# Havok in Gamebryo (Oblivion): what the files and the executable contain

Goal of this whole physics area: **recover the subset of Havok-facing semantics a port needs for gameplay compatibility**, not Havok. No Havok binaries, SDK material, MOPP cooker or decompiled game code live here. Companion files: `character-controller-and-stairs.md` (player body, stairs, symptom checks) and `physics-backend-translation.md` (what to preserve, Bullet mapping, workflow). Retrieval: `hub.py graph show subsystem:collision`, `hub.py tried "<idea>"`.

Evidence tags used below: **[static]** read from the executable or data without running it, **[verified]** measured with an oracle, **[documented]** stated by an upstream source we read but did not check, **[inferred]** our reasoning from evidence, **[guessed]** unchecked. Builds: the Steam retail Oblivion.exe (PE timestamp 0x462392c7) for class facts; the owner's Vilverin visual slice (six stair NIFs and a census of 1,245 parsed NIF headers, version 20.0.0.4, user version 10/11) for data facts. A fact about that slice is not a fact about all of Oblivion or about other Gamebryo games.

## How the layers fit
- Gamebryo owns the visible scene graph (`NiNode`, `NiTriStrips`...). A collidable node carries a **`bhkCollisionObject`** that references a **`bhkRigidBody`**, which holds the Havok **shape**. The executable's `bhk*` classes are the Gamebryo-side wrappers around Havok's `hk*` classes (85 `bhk*`, 51 `hk*`, 5 `Havok*` classes) [static].
- The wrapper layer names: collision objects (static, phantom `bhkSPCollisionObject`/`bhkPCollisionObject`, blend/ragdoll `bhkBlendCollisionObject`), shapes (MOPP tree, tri-strips, packed tri-strips, convex vertices, box, capsule, list, sphere, plane, cylinder, height fields), phantoms (AABB, simple-shape, caching-shape), listeners (water, wind, trap, telekinesis, arrow target, character), a collision filter class, actions (springs, dashpots, motors) and a constraint family: ball-and-socket, hinge, limited hinge, prismatic, ragdoll, stiff spring, malleable, fixed, generic, wheel, breakable [static; names only, behaviour not read].
- A class existing in the executable does not mean any shipped NIF instantiates it. Census the data (below) before building a feature for a class.

## The serialized chain for static architecture
`BSXFlags` + visible `NiTriStrips` + `bhkCollisionObject` -> `bhkRigidBody` -> `bhkMoppBvTreeShape` -> `bhkNiTriStripsShape` -> `NiTriStripsData` (the collision vertices). All six stair meshes of the slice use exactly this chain [verified]. Doors differ: each gate leaf is a `bhkBoxShape` on a `bhkRigidBodyT`, layer 2, motion 6 (keyframed), quality 2, mass 0 [verified].

Aggregate census of the parsed slice (files containing the block): `bhkCollisionObject` 896, `bhkRigidBody` 609, `bhkRigidBodyT` 317, `bhkConvexVerticesShape` 415, `bhkNiTriStripsShape` 240, `bhkMoppBvTreeShape` 237, `bhkBoxShape` 214, `bhkCapsuleShape` 114, `bhkListShape` 102, `bhkConvexTransformShape` 62, `bhkBlendCollisionObject` 26 files (625 blocks), `bhkSPCollisionObject` 8, `bhkPackedNiTriStripsShape` 0. 318 parsed files carry no `bhk*` block at all, and 74 headers did not parse, so the counts are lower bounds [verified for the slice].

## Units and scale (per shape class, not per file)
- Havok-space values in Oblivion are about 1/7 of game units: the controller hull read from the running exe divided by its own scale constant gives 20.25 and 128 units, and box half-extents times 7 reproduce the visible gate slabs [verified, finding `oblivion-havok-unit-scale-about-7`]. The niftools factor of 7 for packed Havok vertices agrees [documented].
- `bhkNiTriStripsShape` vertices (in `NiTriStripsData`) were already in mesh units on the six stairs, so the factor must **not** be applied: collision bounds match the visible mesh on four of six, MOPP scale is 1, strip scale (1,1,1,0) [verified; the x7 attempt came out seven times too large, EXP-OO-004]. Packed strips would use the factor, but none occur in the slice [documented; unmeasured here]. Convex vertices and capsules are unmeasured [guessed: expect x7 like other Havok-native values; compare bounds before assuming].
- Do not apply the rigid-body translation when importing the stair strips: bounds already match without it [verified on four stairs].

## Layers, filters, materials
- The **layer** is a byte inside the body's `HavokFilter` (niftools `OblivionLayer`); the **material** is a separate field (`OblivionHavokMaterial`, e.g. 15 = stone stairs). They are not the same thing: the stair meshes use layer 1 (`OL_STATIC`) with a stone material and none uses `OL_STAIRS` (19) [verified for the six stairs].
- Values cited by the OpenOblivion research from niftools `nif.xml`: `OL_STATIC` 1, `OL_ANIM_STATIC` 2, `OL_CLUTTER` 4, ragdoll limbs on 8, `OL_TRIGGER` 12, `OL_TERRAIN` 13, `OL_NONCOLLIDABLE` 15, `OL_STAIRS` 19, `OL_CHAR_CONTROLLER` 20, pick layers `OL_CAMERA_PICK` 24 through `OL_PATH_PICK` 27 [documented]. See `nif.xml` for the full list; do not copy it blindly.
- Which layers block which is a **filter matrix inside Havok** (`bhkCollisionFilter`); it was not recovered. "World surfaces a character stands on are 1, 2, 13 and 19; triggers, non-collidable and pick shapes must not become floors" is a sensible reading of the names [inferred]. A translator should filter by layer (accept layer 1 only for the first strip loader) and keep the render-mesh fallback explicit and logged.

## Motion types and quality
Static architecture is fixed motion with fixed quality (motion 7, quality 1); animated doors are keyframed (motion 6, quality 2); clutter is dynamic; ragdolls use the blend collision object [documented for the meanings; verified for the stair and gate values]. Mass 0, friction 0.3 and restitution 0.3 were read on the stair bodies [verified].

## MOPP
A MOPP tree is Havok's bounding-volume tree code wrapped around a child shape, built by Havok's own tool [documented]. It is an acceleration structure: importing the child triangles into a BVH of your own needs neither executing the bytes nor the cooker [inferred, finding `mopp-bytecode-not-needed-for-static-import`]. Not tested: whether a MOPP built from a subset or with different welding changes query results against the full triangle set.

## Triggers, phantoms, constraints, terrain
- Phantoms report overlap without pushing; `bhkSPCollisionObject` carries trigger volumes (8 files in the slice) [documented]. In a translation keep overlap events and drop contact response.
- Ragdolls and constraints belong to the blend collision object and the constraint family; the capsules in the skeleton are layer-8 ragdoll limbs, not the player controller [documented, verified for the skeleton].
- Height-field shape classes exist (`hkBSHeightFieldShape`, a tri-sampled height-field tree) [static]. How exterior terrain collision is built (height field versus mesh) was not investigated: **open question**.

## Authored collision is not render geometry
Authored collision of the stair meshes has about half the triangles of the visible mesh, and ray-grid heights differ (arwhallstairs01 median 2.32 units, maximum 372.7 over 245 paired rays; arnhallstairs01 median 0.55) [verified, EXP-OO-003]. Two meshes (U-turn, pit) differ in bounds by a few percent for the same reason. A donor engine that builds collision from visible geometry (OpenMW at the 0.52 pin: BSXFlags bit 2 -> render geometry; the reader parses `bhk*` blocks but the loader ignores them) therefore has a different floor [static, project-scoped]. Whether that difference changes stair feel was **not** measured with a character controller.

## Census recipe (cheap, no game data committed)
Parse every NIF header with a reader that supports the version, count `bhk*` block types per file, record per-body layer, motion, quality, mass and shape scale, then for each mesh compare collision bounds with visible bounds per axis. Publish counts and rules, never the files. Oracle for a reading: bounds equality or a constant ratio, plus a ray grid on the shapes.

## Open questions
Packed-strip prevalence outside Oblivion [guessed: heavier in later games; census first]; the layer filter matrix; terrain height-field use; convex/capsule scale; exact Havok world step rate and solver settings; collision materials' gameplay effects (sounds, friction).

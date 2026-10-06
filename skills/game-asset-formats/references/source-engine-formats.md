# Source engine formats (MDL v49 family), condensed

From universal-modder's technique note "Reading Source engine (MDL v49) models, textures and animations in plain Python, no SDK" (MIT; verified on Left 4 Dead 1 by an agent; read in the corpus). Paraphrased. MDL versions 44-48 should be similar but were not tried; check struct sizes on your files.

## VPK
Read the `_dir.vpk` tree once: extension -> directory -> file name, each zero-terminated; each entry has CRC, preload size, archive index, offset, length, then optional preload bytes. Archive index `0x7fff` = data stored after the tree inside the dir file. Content is spread over `_000.vpk`, `_001.vpk`... (headerless chunks). Check every `_dir.vpk` and then loose files on disk (some games keep sounds loose).

## Model = several files with one stem
`.mdl` (skeleton, body parts, materials, sequences), `.vvd` (vertices), `.dx90.vtx` (triangle indices); animated characters include `anim_*.mdl` and often a `.ani`.

## MDL header and records
Fixed header holds counts/offsets for bones, local animation descriptions, sequences, textures, texture dirs, skin table, body parts, included models, animation blocks. Record sizes (v49): bone 216, body part 16, model 148, mesh 116, texture 64, sequence desc 212, animation desc 100. Strings are offsets relative to the owning record.

## Geometry
- VVD vertex = 48 bytes: 3 bone weights, 3 bone indices, bone count, position, normal, UV. With a fixup table, LOD 0 = concatenation of every fixup range with LOD number >= 0 in table order.
- VTX (byte-packed): body part 8, model 8, LOD 12, mesh 9, strip group 25, strip 27 bytes (some later v49 builds, e.g. Source Filmmaker, add two ints to strip group and strip: 33/35; verify the next record starts where the size says). Vertex list entries are 9 bytes (use the original-mesh-vertex id); indices 16-bit triangle lists. Final index = model vertex start (byte offset / 48) + mesh vertex offset + VTX vertex id.
- Characters have body parts with interchangeable models (heads, bodies); choose one per part. Material number -> skin table -> texture index (many skin families).

## Textures
Material path = texture dir + material name; the VMT's base-texture entry (maybe through an include) names the VTF. VTF mips are stored smallest first: the largest image is the **last** block; reach any mip by summing sizes from the end. Decode DXT1/3/5 and uncompressed BGRA/RGB yourself; a lower mip gives a smaller texture without resizing. Alpha is often a tint/specular mask.

## Skeleton and skinning
Bone: parent, local position, quaternion (x,y,z,w), stored pose-to-bone 3x4 (inverse bind). Check: world bind x pose-to-bone = identity for every bone; skinned vertices equal raw positions. If both pass, trouble is in animation decode, not skeleton.

## Animation
- Sequences/animation descriptions live in the model and every included model; included models have their own (smaller) skeleton: map bones by name; unmentioned bones keep the main reference pose.
- Block number says where data is: 0 = inside the MDL (relative to the description); otherwise index a table of (start, end) pairs into the `.ani`, offset relative to the block start.
- Long clips are cut into sections of N frames: section = frame / N, remainder inside; last frame lives in an extra final section.
- Locomotion sequences use a blend grid (e.g. 3x3 animations); pick the cell deliberately (straight-ahead run was index 1; middle cell was standing).
- Storage styles (animation flags): *bone by frame* (flag 0x40 clear): chain of entries {bone, flags, next offset}; rotation raw 48-bit quaternion (three 16-bit, third has 15 bits + sign for W), raw 64-bit (three 21-bit + sign), position as three half-floats, or animated channels (offsets to RLE 16-bit runs: (valid, total) then `valid` values; value x bone scale + bone default; animated rotation is Euler -> quaternion). *Frame by bone* (0x40 set): header (constant block offset, per-frame block offset, bytes per frame), a flag byte per bone, constants, then per-frame records.
- Delta/additive clips (flag 0x04, or 0x44 when frame-by-bone): skip unless you implement additive blending. `Name_Layer` clips set only some bones and are overlaid on a looping base clip; the clip named `Name` can be an empty stub: count bones touched while decoding.
- Source characters are authored lying down; animations stand them up. Pose with an animation (even one idle frame) rather than rotating the model.

## Oracles that worked
Skeleton/skinning identity check; silhouette renderer in three orthographic views; bounding boxes per clip (orders of magnitude off = wrong storage style); freeze the target game and step a few ticks with screenshots. Not verified: IK, additive clips, facial flex, physics bones, animated textures.

## Common gotchas (symptom -> cause -> fix)
Flat character -> authored lying down -> pose with animation. Garbage bounds -> wrong storage style or external `.ani` -> check flags/block first. Attack looks like run -> stub clip -> use `_Layer`. Missing hands/collars -> alpha is a mask -> opaque unless flagged. Wrong face texture -> skin family -> choose family. Huge vertex files -> unused LOD vertices and full-rate frames -> prune/renumber, thin frames. Walk goes wrong after record 1 -> struct size off -> print the next record's name after each walk.

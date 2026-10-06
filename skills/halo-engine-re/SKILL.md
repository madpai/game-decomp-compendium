---
name: halo-engine-re
description: Knowledge for working with Halo's Blam engine and data: Halo CE tag system and cache (.map) files, scenario/BSP/objects/units/AI/HaloScript module map from the Halo CE decompilation, Halo 3 MCC map reading with Reclaimer and tag field layouts, units and axes, sound banks, and how Halo content relates to Source-engine imports. Use for any Halo CE/Trial/MCC/Reach task: parsing tags or maps, extracting models/animations/scenarios, understanding AI or scripting behaviour, building or porting a Halo-compatible engine (open reimplementations, Android ports), converting content between Halo and other engines, or finding the right decomp/reference project. Also covers what NOT to publish (game data, Trial files).
---

# Halo engine reverse engineering

Start with `python3 ../gamedecomp-library/scripts/hub.py prior-art "halo <topic>"`. Relevant sources in the corpus: the Halo CE decompilation (`punpckhdq/halo`, CC0, build 2342 Xbox `cachebeta.exe`), a second Halo CE decomp (`halo-re/halo`, listed only), Halo Reach (`ChimpsAtSea/Reach`, GPL-3.0), a Halo 3 cache-release recomp (`twist84/...`, human-only AI policy: not ingested), and universal-modder's Halo 3 MCC field note (MIT).

## Mental model of the engine
Blam is **data-driven**: gameplay content is a graph of *tags* (typed data files) compiled into a per-scenario *cache map*. Code is a runtime that interprets tags: objects/units/items/devices, AI actors and encounters, physics and models, BSP structures, the renderer/rasterizer, sound, effects, and HaloScript (`hs`) bytecode attached to scenarios. To port or reimplement, parse the tag/cache formats first, then implement systems in the decomp's module order (below). The decomp's file layout is itself a map of the original source tree: `ai bink bitmaps bungie_net cache camera cseries cutscene devices dialogs editor effects game hs input interface items main math memory models networking objects physics rasterizer render saved films saved games scenario shaders shell sound strings structures tag_files text tool units`.

## Tag system essentials (from the decomp's `tag_groups.h`)
- A **tag group** is identified by a 32-bit four-character code (`weap`, `proj`, `mode`, `sbsp`, `scnr`, `jpt!`, `hlmt`, `char`, `bitm`...). A tag is a tree of **blocks**.
- Runtime structures: `tag_block { long count; void* address; definition* }`, `tag_reference { group_tag, name pointer, name_length, index }`, `tag_data { size, pad, file_offset, address, definition }`. Blocks are arrays of fixed-size elements with a maximum element count; fields are described by `tag_field {type, name, definition}`.
- The field-type enum (use it to write a generic parser or a layout dumper): string, char/short/long integer, angle, tag, enum, flags (long/word/byte), point2d, rectangle2d, rgb/argb pixel32, real, real_fraction, real point/vector 2d/3d, quaternion, euler angles 2d/3d, plane 2d/3d, rgb/argb/hsv/ahsv colors, bounds (short/angle/real/real_fraction), tag_reference, block, short/long block index, data, start_array/end_array, pad, skip, explanation, custom, terminator (44 types). Padding/skip fields are how layouts stay offset-stable: honour them exactly.
- Block definitions carry callbacks (byte swap, postprocess, format, delete). The decomp keeps byte-swap codes per block, so the same definitions can read data of either endianness; confirm the layout of each platform's cache (Xbox, PC, MCC) before assuming identical field offsets.
- `cache_files.h`: `scenario_tags_load(name)`, `scenario_structure_bsp_load/unload`, map-file precache states, `tag_get_group_tag(tag_index)`; a map is checksummed (`cache_files_get_checksum`).

## Module guide (where to read for X)
| Need | Decomp directory |
|---|---|
| Actor types and behaviours (elite, grunt, jackal, hunter, flood, sentinel, marine, engineer, crew, carrier, mounted weapon), actions (alert, avoid, charge, converse, fight, flee, guard, obey, search, sleep, uncover, vehicle, wait), encounters, perception, firing positions, pathfinding (obstacle avoidance, smoothing, BSP paths), AI scripting hooks | `ai/` |
| HaloScript: compile (`hs_compile.c`), runtime (`hs_runtime.c`), builtin functions and globals (`hs_library_*`, `hs_globals_external.c`), scenario script definitions | `hs/` |
| Scenario (`scnr`) placement, sky, fog, wind, multiplayer descriptions | `scenario/` |
| Objects/units/items/devices | `objects/ units/ items/ devices/` |
| Map loading and resource caches (textures, sounds, predicted resources) | `cache/` |
| Tag IO and groups | `tag_files/` |
| BSP structure, collision, physics, models, rendering | `structures/ physics/ models/ render/ rasterizer/` |
| Networking, saved films, cutscenes, interface | `networking/ saved films/ cutscene/ interface/` |
Read headers first (they are small and name the public API), then the `.c` for behaviour. Use `hub.py show project:punpckhdq--halo` for build notes.

## Build and decomp facts
Halo CE decomp: target `cachebeta.exe` (build 2342, hash in its README), Xbox SDK (Aug 2001) compiler and `ninja` via `configure.py` + `tools/project_x86.py`, `csplit`-based splitting, objdiff for diffs, progress on decomp.dev (~15% when read). Type information comes from debug symbols of *later* Halo games turned into headers with `pdb-decompiler` (Halo CEA beta); CEA derives from Halo PC so it is not 100% faithful to the original Xbox title: treat recovered types as hypotheses. See `decomp-matching-workflow`.

## Halo 3 (MCC) reading notes (field note `halo-3-weapons-covenant-vehicles-and-maps-ported-into-minecr`)
- MCC is two engines in one install: an Unreal shell (`mcc-win64-shipping.exe`) and the Blam gen3 game DLL with `halo3\maps\*.map` caches. Anti-cheat protects the shell: **read the files on disk only; never launch, attach to or modify the running game**.
- **Reclaimer** (C#/.NET 9) opens MCC Halo 3 maps headless (`CacheFactory.ReadCacheFile`; geometry providers for `mode` render models, `sbsp` BSP, `scnr` scenarios; `WriteRMF` exports a neutral mesh format readable by a pure-Python importer). From Python use pythonnet with a runtimeconfig naming only the base framework; never return WPF-typed objects (e.g. `DdsImage`) to Python; use `__implementation__` on interface handles.
- Units/axes: positions already in Halo world units (1 wu = 3.048 m; do not multiply by the scene's mm-per-wu field); X forward, Y left, Z up; row-vector matrices (`pos @ vertex_transform @ permutation.transform`; `uv @ texture_transform`); bone world = local_bone @ ... @ local_root.
- Skeleton: biped bones named pelvis/spine/spine1/head/l_upperarm/l_forearm/l_hand/l_thigh/l_calf...; bind pose has arms down with elbows bent ~90 degrees forward; vehicle wheels `lf/rf/lb/rb_tire`.
- Materials: usages `diffuse`, `color_change` (R = armour tint mask: bake `diffuse * lerp(1, colour, mask)` per rank), `blend`, `self_illum`; diffuse alpha is often a specular mask (force opaque for opaque materials). BSP terrain shaders blend 2-4 layers by a blend map (`blend_channel` 1/2/4/8 = R/G/B/A).
- Raw tag fields: tag block = `{int32 count, int32 pointer, int32 pad}`; address via the translator after pointer expansion (MCC Halo 3 expands `ptr << 2`); tag references are 16 bytes with the tag index in the low 16 bits at +12; field offsets come from Assembly's `Plugins/Halo3MCC/*.xml`. Damage and vitality share "Halo points" (MP Chief body 45 + shield 70; AR bullet 7.5; BR 6; sniper 80).
- Sound: effects live in an FMOD FSB5 bank (`sfx.fsb`, Vorbis); `sfx.fsb.info` has 280-byte records in the same order with the original source path at +24, mapping samples to sound tags; decode with vgmstream (subsong = index + 1).
- Campaign vs MP content: weapons, vehicles, MP Chief/Elite are in MP maps (riverworld suffices); Covenant and Marine models live in specific campaign maps (e.g. `030_outskirts`, `040_voi`, `050_floodvoi`).
- Grenade timers start on bounce/rest, not on throw; Jackal "shield vitality" is its gauntlet (frontal armour); both are examples where raw tag numbers mislead without the engine rule.

## Halo <-> Source/other-engine content
Mapping Source (MDL/VVD/VTX/VTF/VPK/BSP) or other formats into Halo-compatible engines needs the parsers and self-checks in `game-asset-formats` (skeleton identity check, silhouette renderer oracle, animation storage styles, layer/delta clips). Keep Halo's own sky/style decisions as the owner specifies in the project docs.

## Guardrails
- Game data (maps, Trial files, extracted assets, bitmaps, sounds) is never committed or published; derive it locally from the user's own install.
- Do not touch MCC while it runs (EasyAntiCheat). No multiplayer cheating tools.
- Project-specific rules (what may go into which repo, test routines) live in each project's `CLAUDE.md`/`docs/HANDOFF.md`; read those before editing.

## Files
- `references/halo-sources-and-tools.md`: catalog entries, community tools (HEK Guerilla/Sapien/Tool, Invader, Assembly, Reclaimer, pdb-decompiler, vgmstream), and licences.

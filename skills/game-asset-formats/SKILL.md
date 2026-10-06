---
name: game-asset-formats
description: How to read, convert and safely parse game asset and container formats: identify unknown files (magic/entropy), reverse-engineer an undocumented format and prove it with a round trip, parse archives (BSA/BA2, VPK, pak/IoStore, BND/DCX, Unity bundles), meshes/skeletons/animations (Source MDL/VVD/VTX, NIF, FLVER), textures (DDS/VTF/KTX), audio banks (FSB/Wwise/CRI), maps (BSP, Halo cache), with bounded, fuzz-tested parsers (binrw, Kaitai). Use for any task that involves unknown binary files, extracting or converting game assets from the user's own install, writing a parser/writer, porting content between engines (Source -> Halo, Unity -> Minecraft...), or choosing the community tool for an engine's formats.
---

# Game asset formats

Rule zero: **read the real files, never guess.** The data on disk is the spec; every claim about a format needs a mechanical check (parse all stock files without error, decode to something you can look at, round trip). Assets come from the user's own install; converters run on the user's machine; nothing from the game is committed or published.

## 1. Identify
`python3 scripts/identify.py <path> [-r] [--summary] [--hex N]` classifies files by magic bytes and entropy (archives, textures, meshes, sound banks, executables, engine data, compression). Unknown + high entropy (>7.5) on a non-compressed type = compressed or encrypted: identify the wrapper first (Oodle/zlib/lz4/LZX; keys are usually in the exe or public). Extension lies; magic and structure do not. Numbered `_000.vpk` style files are headerless data chunks of a `_dir` index.

## 2. Use the community tool before reversing
Search `python3 ../gamedecomp-library/scripts/hub.py search "<engine> <format>"` and `references/engine-format-tools.md`. Most formats from the 2000s-2010s are documented (XeNTaX/ZenHAX archives, UESP, Valve Developer Wiki). Use community knowledge and tools regardless of origin, but do not download game files, leaked code, SDKs or keys from them.

## 3. Reverse an undocumented format (method)
1. Collect many stock files; compare sizes; hex-dump headers; find magic, counts, offsets, tables of fixed-size records, strings, alignment.
2. Hypothesise header -> record layout -> compression. Prove by parsing *every* stock file without error and without leftover bytes.
3. Write a reader that decodes to something viewable (PNG, OBJ/GLB, JSON, WAV) and **look at it**: a silhouette/orthographic renderer is the fastest oracle for geometry and animation (a wrong decode appears twisted or huge immediately; also plot bounding boxes).
4. Write the writer and **round trip**: decode -> encode -> decode, compare to the original (AoE2's SLD sprite writer was accepted at 0.9/255 mean error).
5. Only then write new files; test with one asset in the real game before batch conversion.
Numeric self-checks beat eyeballing: e.g. every bone's world bind matrix times its stored pose-to-bone matrix must be the identity (worst error ~1e-6); skin all vertices and compare to raw positions (~1e-5).

## 4. Parser safety and quality (from unity-rs's AGENTS.md and binrw practice)
Treat every file, archive name, offset, count and schema as untrusted:
- checked arithmetic for offsets/sizes/counts/strides; bound individual and cumulative input, allocation, decompression, traversal and output; fallible reservation before growing buffers from input counts; no unbounded `read_to_end`;
- validate a complete known layout and reject unverified tails/versions instead of partially parsing; keep error families distinct (InvalidData vs Unsupported vs limit vs I/O); no silent fallbacks that turn corrupt input into plausible output;
- fixtures before claims: a version/format is "supported" only with verified fixtures; private real-asset corpora stay out of git; opt-in acceptance harness; differential oracle against a reference implementation where one exists;
- tools: `binrw` (declarative magic/endianness/padding/offset/validation), Kaitai Struct specs (`.ksy`, used by isle), `proptest`/`cargo-fuzz` for hostile inputs, `insta` snapshots for stable outputs, `criterion` for speed.
See `references/parser-safety-and-testing.md`.

## 5. Format cheat sheets in this skill
- `references/source-engine-formats.md`: VPK, MDL/VVD/VTX v49, VTF, skeleton/animation decode (two storage styles, `.ani` blocks, sections, layer/delta clips), proven on Left 4 Dead; use for Source -> other-engine imports.
- `references/engine-format-tools.md`: per-engine containers, community tools and libraries (Bethesda, Unity, Unreal, FromSoftware, Source, GameMaker, Godot, Genie, Halo, RPG Maker...).
- Bethesda formats: `bethesda-gamebryo-re/references/tes4-formats.md`. Halo caches/tags: `halo-engine-re`.

## 6. Conversion pipeline pattern (works for Source->X, Halo->X, Unity->X)
`reader (verified)` -> `neutral intermediate (positions/normals/uv/bone weights/frames, PNG textures, JSON stats)` -> `writer for the target engine`. Keep one frame-mapping function (axes, scale, handedness) shared by both sides; bake animations to per-frame vertex positions only if the target lacks skinning; thin frames and dedupe vertices (LOD copies are never referenced; dropping them cut one mesh file to a third); make alpha handling explicit (alpha is often a tint/specular mask: treat opaque unless the material says alpha-test/translucent); choose skin/material families deliberately; keep placeholders so the target works when the private converted pack is missing.

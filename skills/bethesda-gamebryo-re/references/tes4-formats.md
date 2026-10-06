# TES4 (Oblivion) file formats: what is verified, and where to read more

Evidence tags: **[M]** measured on a retail Oblivion.esm / BSAs in this project; **[S]** from source of a maintained library (esplugin GPL-3.0, bsa-rs 0BSD) read in the corpus; **[D]** documented by the community (UESP/CS wiki) and consistent with [M]/[S] where tested; **[?]** inference or unverified.

## Plugin files (.esm/.esp)
- **Record**: header **20 bytes** [M][S]: type(4) dataSize(4) flags(4) formID(4) versionControl(4), then `dataSize` bytes of subrecords. **GRUP**: header 20 bytes: `GRUP`, groupSize (includes header), label(4), groupType(4), stamp(4); children follow. (Fallout 3/NV/Skyrim headers are 24 bytes [S].)
- **Subrecord**: type(4) size(2) data; `XXXX` precedes an oversized subrecord and carries its 32-bit size [M: handled by the project's parser].
- **Flags** [M][D]: bit 0 master (TES4 header record), `0x20` deleted, `0x40000` compressed: payload = 4-byte uncompressed size + zlib stream [M: handled].
- **FormID**: high byte = index into the plugin's master list (MAST subrecords, in order; own records use index = number of masters); mask with `% 0x1000000` to strip it for per-file ids [M: bug found when comparing ids].
- Header record `TES4` with `HEDR` (version float, record count, next object id) [M for presence of HEDR].
- Top-level groups of interest: QUST (quests; stages in INDX/QSDT/CNAM/SCDA), DIAL (topics, with child GRUP type 7 containing INFO responses), SCPT (scripts), REFR/ACHR/ACRE (placed references), CELL/WRLD, NPC_, RACE, TREE (SpeedTree records) [D].

## Scripts (SCPT, and result scripts in INFO/QUST stages)
- Subrecords: SCHR (header: unused, ref count, compiled size, variable count, type object/quest/effect), SCDA compiled bytecode, SCTX source text, SLSD/SCVR local variables, SCRO referenced forms [D/M]. Every script in Oblivion.esm keeps its source beside the bytecode [M].
- Bytecode: `ScriptName`/`Begin <Block>`/`End`, `If/Elseif/Else/Endif`, `Set`, command calls with parameter lists, reference prefix opcode `0x1C` [M]. Command opcodes 0x1000-0x1171 index the exe's command table (see SKILL.md) [M].
- A compiler built from the table (parameter types and optional flags per command) reproduces the original's statement-level opcode sequence for all 7,945 scripts with both source and bytecode [M]; the original compiler ignores extra words after a command [M].
- Block types and semantics (GameMode every frame-ish, OnActivate replacing default activation unless the script calls Activate, OnLoad, OnDeath, OnHit...) are [D]; OpenOblivion runs GameMode at 0.25 s and logs unimplemented commands once [choice].

## Conditions (CTDA) and dialogue
- CTDA = **24 bytes** in Oblivion [M: 48,531 of 48,531]: type(1) unused(3) comparison float(4) function(4) param1(4) param2(4) unused(4, nonzero in 14 cases). Type byte: `0x1` OR with next, `0x2` run on target, `0x4` use global for comparison value, operator in bits 5-7. 92 distinct functions occur; GetIsID alone is 40%; 14 functions cover 94.6% [M].
- OR-group semantics: conditions AND together except OR-flagged ones joined to the following condition; a trailing OR leaves an open group (the project treats it as open) [? semantics verified only structurally; FNV's reconstructed `TESCondition` has a `ForceTrailingAnd` normaliser, a hint that the editor avoids trailing ORs].
- Dialogue: INFO responses of a DIAL topic are tried in file order and the first whose conditions pass is used; random flag chooses among passing random ones; say-once responses are skipped after use; topic list contents depend on learned topics (AddTopic / add-topic lists) [D, partially verified against behaviour; list rule is unmeasured [?]].
- Quests: stage entries (INDX) carry journal text and result scripts; `SetStage` on a not-running quest starts it [? inferred].

## BSA archives (Oblivion = version 103)
Read in `bsa-rs` (0BSD) [S]: magic `BSA\0`, header size **0x24**; versions 103 (Oblivion; zlib), 104 (FO3/FNV/Skyrim LE), 105 (Skyrim SE; lz4). Archive flags: bit0 directory names present, bit1 file names present, bit2 compressed by default, bit3/4 retain dir/file names, bit5 retain file-name offsets, bit6 Xbox archive, bit7 retain strings during startup, bit8 embedded file names (v104+), bit9 Xbox compressed. File-type flags: meshes, textures, menus, sounds, voices, shaders, trees, fonts, misc. Per-file size field bit 30 toggles compression relative to the archive default. Names are hashed [S] (directory and file hashes; CRC step `h = byte + h*0x1003F`) and records are sorted by hash [D]; lookups use the hash, so names are lowercased and normalised to the archive's separator convention before hashing [S/D]. Voices live in `Oblivion - Voices1.bsa`/`Voices2.bsa` under `sound/voice/oblivion.esm/<race>/<m|f>/`; DLC voices in their own BSAs [M].
Tools: `ba2` (bsa-rs) for Rust, `rust-bsa-ba2-handler` CLI (MIT), BSArch (CLI), the project's own `bsa.py`.

## Meshes, textures, faces, trees [D/?]
NIF (Gamebryo; Oblivion files are version 20.0.0.4/20.0.0.5 with Bethesda user versions) edited with NifSkope; textures DDS (BC1/BC3); facegen `.egm/.egt/.fgm`; SpeedTree `.spt` for trees with the `SpeedTree*` shader classes in the exe (the OpenOblivion tree billboards work from `.spt` data and a patched OpenMW shape manager). Verify NIF header versions on your files before choosing a parser.

## Load order
Plugin list = `Plugins.txt` (active) plus timestamp/`DLCList.txt` rules for masters first; `libloadorder` (GPL-3.0) models Oblivion and OpenMW load order and ships an mdbook on the subject; LOOT sorts using `esplugin` metadata [S].

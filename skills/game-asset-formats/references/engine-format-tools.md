# Containers, formats and community tools by engine

Condensed from universal-modder's engine playbooks and `reverse-engineering` skill (MIT) and the compendium's Rust/C#/Python library entries (`hub.py search "<name>"`). Check each tool's repository for current versions.

| Engine / game family | Containers and formats | Read/convert with |
|---|---|---|
| Bethesda (Gamebryo/Creation) | `.esm/.esp/.esl` records, `.bsa` (v103 Oblivion, v104 FO3/FNV/Skyrim LE, v105 SSE), `.ba2` (FO4/76/Starfield), `.nif`, DDS, `.egm/.egt/.fgm`, voices mp3/lip | xEdit/TES4Edit, `esplugin` (GPL-3), `ba2` crate (0BSD), BSArch, NifSkope, PyNifly, `libloadorder` |
| Unity | UnityFS bundles, serialized files, `globalgamemanagers`, IL2CPP `global-metadata.dat` | UABEA, AssetRipper, UnityPy, `unity-rs` (3 Rust variants), Il2CppDumper, Cpp2IL, ILSpy |
| Unreal 3/4/5 | `.pak`, IoStore `.utoc/.ucas`, `.uasset/.umap/.uexp`, `.usmap` mappings | FModel (CUE4Parse), UAssetGUI/UAssetAPI (human-only AI policy), `repak`, `retoc`, UnrealPak, UE4SS/Dumper-7 for reflection; UE3 offline notes in universal-modder |
| FromSoftware | BND3/BND4, DCX, BDT, FLVER, PARAM/MSB/TAE/FMG | SoulsFormats (C#), `soulsformats-rs`, WitchyBND, Smithbox, Paramdex defs |
| Source 1/2 | VPK, MDL/VVD/VTX/ANI, VTF/VMT, BSP, VMF, Source 2 `_c` resources | Crowbar, VPKEdit/GCFScape, VTFEdit, BSPSource, VRF (Source 2 Viewer), `plumber-core`, `vbsp` (Rust BSP parser) |
| Halo (Blam) | tags + cache `.map`, FMOD FSB5 banks (MCC) | Reclaimer, Assembly, HEK tools, vgmstream (see `halo-engine-re`) |
| .NET/XNA/FNA | `.xnb` content (often LZX-compressed), managed DLLs | XnbExtract/XNA tools, ILSpy, tModLoader/SMAPI tooling |
| GameMaker | `data.win` (FORM), `game.unx` | UndertaleModTool (CLI exists) |
| Godot | `.pck`, `.gd` | GDRE Tools |
| RPG Maker | MV/MZ JSON + encrypted `.rpgmvp`; XP/VX/VX Ace `Scripts.rxdata`, RGSSAD | decrypters/extractors, EasyRPG liblcf |
| Ren'Py | `.rpa`, `.rpyc` | unrpa, unrpyc |
| Genie (AoE2) | `.dat`, `.sld`, scenarios | genieutils-py, AoE2ScenarioParser |
| id Tech/Doom/Quake | WAD/PK3/PAK | SLADE, Ultimate Doom Builder, GZDoom |
| Electron/NW.js/HTML5 | `app.asar`, `package.nw` | `@electron/asar`, devtools |
| LÖVE / Java / Defold / Cocos | zip `.love`, jars, `game.arcd`, XXTEA bundles | unzip, Vineflower/CFR/Recaf, unpackers |
| CRI middleware | CPK archives, `@UTF` tables, HCA audio | CriPakTools/vgmstream |
| Nintendo | SARC, Yaz0, U8, BNTX, BFRES | community tools in the decomp projects' `tools/` |
| Wwise / FMOD | `.bnk/.pck`, `.fsb` | wwiser/vgmstream, FMOD tools |

## Historical format knowledge
XeNTaX (forum, wiki, attachments archived on archive.org; GitHub backup), ZenHAX (QuickBMS scripts, posts to early 2023), "The definitive guide to exploring file formats" (XeNTaX). Use for format knowledge and tools; never download game files, leaked code/SDKs or license keys from them.

## Reading plan
1. `identify.py` on the install to inventory formats.
2. For each unknown family: community tool -> documentation -> your own reader with self-checks.
3. Convert on the user's machine into a private cache; keep derived data out of repositories.

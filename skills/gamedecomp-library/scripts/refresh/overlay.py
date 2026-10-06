#!/usr/bin/env python3
"""Hand-curated overlay for the catalog: why an entry matters, which skill covers it, how deeply it was read, AI-contribution policy.
depth: deep = cloned and source/docs read; readme = README read; meta = catalog metadata only.
ai: human-only | no-ai-decomp | disclose | ai-ok | mentions (README mentions AI; read CONTRIBUTING before contributing) | unspecified
"""
import json, sys
O = {}
def add(i, use, note, depth='readme', ai=None):
    O[i] = {'use': use, 'note': note, 'depth': depth}
    if ai: O[i]['ai'] = ai

# ---- runtime modding / RE libraries -------------------------------------------------------------
add('vswarte--fromsoftware-rs', ['game-hooking-patterns','re-binary-recon'], 'Pattern library for runtime modding of x64 MSVC games: RTTI-derived class bindings, FromStatic/FromSingleton lookup, AOB->RVA "binary mapper" with TOML profiles + RVA regression tests, param-generator, hooks on the main-thread task system, DllMain+hudhook+ilhook mod template, MSVC STL layouts, Superclass/Subclass vtable checks.', 'deep')
add('tremwil--vtable-rs', ['game-hooking-patterns'], 'Rust macro for declaring C++ vtable layouts, virtual-call wrappers and Rust-implemented subclasses of C++ classes.', 'deep')
add('dasaav-dsv--from-singleton', ['game-hooking-patterns'], 'Finds game singletons by (RTTI) class name at runtime instead of hard-coded addresses.', 'deep')
add('dasaav-dsv--liber', ['game-hooking-patterns'], 'C++ API/bindings for FromSoftware games.')
add('homoradahn--soulsformats-rs', ['game-asset-formats'], 'Rust parsers for FromSoftware container/data formats.')
add('soulsmods--soulsformatsnext', ['game-asset-formats'], 'C# FromSoftware format library (reference implementation for BND/DCX/PARAM/FLVER-style formats).')
add('jkanderson--soulsformats', ['game-asset-formats'], 'C# FromSoftware format reference.')
add('vawser--paramdex', ['game-asset-formats'], 'Community database of PARAM field names/types: the data-driven way to document a huge table-based game.')
add('vawser--smithbox', ['game-asset-formats'], 'Editor for FromSoftware data; shows what a mature modding editor needs from a format library.')
add('soulsmods--modengine2', ['game-hooking-patterns'], 'Mod loader for FromSoftware games (file overrides, extension DLLs); not read in depth.', 'meta')
add('garyttierney--me3', ['game-hooking-patterns'], 'Rust mod loader for FromSoftware games (catalog: "Rust mod loader"); not read in depth, see its README for the profile/launch model.', 'meta')
add('nordgaren--elden-ring-debug-tool', ['game-hooking-patterns'], 'Debugging tool for Elden Ring (catalog: "Debugging tool"); not read in depth. Online-play/anti-cheat caveat applies: use only offline.', 'meta')
add('trumank--repak', ['game-asset-formats'], 'Rust Unreal .pak reader/writer.')
add('trumank--retoc', ['game-asset-formats'], 'Rust Unreal IoStore (.utoc/.ucas) tool and legacy<->IoStore converter.')
add('atenfyr--uassetapi', ['game-asset-formats'], 'C# Unreal .uasset/.umap API. Project rejects AI-generated contributions.', 'readme', 'human-only')
add('ue4ss-re--re-ue4ss', ['game-hooking-patterns'], 'UE4SS: Lua/C++ scripting and object dumpers injected into Unreal games; reference for reflection-driven modding.')
add('astrotechies--unrealmodding', ['game-asset-formats'], 'Rust toolkit for Unreal asset modding.')
add('maikklein--unreal-rust', ['engine-reimplementation'], 'Rust integration into Unreal Engine.')
add('assetripper--assetripper', ['game-asset-formats'], 'Unity asset extraction tool (C#).')
add('k0lb3--unitypy', ['game-asset-formats'], 'Python Unity bundle/asset reader; fastest way to script-inspect Unity data.')
add('samboycoding--cpp2il', ['game-asset-formats'], 'IL2CPP back to managed assemblies (analysis tool).')
add('perfare--il2cppdumper', ['game-asset-formats'], 'IL2CPP metadata dumper producing headers/scripts for disassemblers.')
add('bepinex--bepinex', ['game-hooking-patterns'], 'Unity mod framework: patch loading, config, plugin lifecycle.')
add('seiunx-dev--unity-rs', ['game-asset-formats'], 'Rust Unity asset reader with an unusually strong AGENTS.md: bounded parsing, checked arithmetic, error families, fixtures-before-claims, corpus harness kept private.', 'deep')
add('yuanyan3060--unity-rs', ['game-asset-formats'], 'Rust Unity asset parser (second implementation).')
add('latias94--unity-asset', ['game-asset-formats'], 'Rust Unity asset toolkit (third implementation).')
add('lasa01--plumber-core', ['game-asset-formats'], 'Rust Source-engine asset conversion library (catalog: "Rust asset conversion library"); clone failed in this harvest.', 'meta')
add('icewind1991--vbsp', ['game-asset-formats'], 'Rust Source BSP map parser.')
add('ryan-rsm-mckenzie--bsa-rs', ['bethesda-gamebryo-re','game-asset-formats'], '`ba2` crate: DOM reader/writer for Bethesda archives, Morrowind through Starfield (TES3, TES4 incl. Oblivion BSA v103, FO4/Starfield BA2). Test suite ported from the C++ original. 0BSD licence = safe to study and adapt.', 'deep')
add('ortham--esplugin', ['bethesda-gamebryo-re'], 'Plugin (.esp/.esm/.esl) parser for Morrowind, Oblivion, Skyrim, FO3/NV, FO4, Starfield; built for LOOT/libloadorder. GPL-3.0.', 'deep')
add('ortham--libloadorder', ['bethesda-gamebryo-re'], 'Load-order and active-plugin handling per game (includes OpenMW and Oblivion); ships an mdbook explaining load orders. GPL-3.0.', 'deep')
add('sulfurnitride--rust-bsa-ba2-handler', ['bethesda-gamebryo-re','game-asset-formats'], 'MIT BSA/BA2 pack/unpack/list/verify CLI+GUI; useful reference for Oblivion BSA v103 (zlib) flag handling.', 'readme')
add('casualx--pelite', ['re-binary-recon'], 'Rust PE parser with a CLI and lightweight pattern scanner; ships AI-writing "skills" files (alpine, unslop).', 'deep')
add('m4b--goblin', ['re-binary-recon'], 'Zero-copy ELF/Mach-O/PE/archive parser (Rust).', 'deep')
add('gimli-rs--object', ['re-binary-recon'], 'Unified object-file reading/writing (ELF, Mach-O, PE/COFF, Wasm, XCOFF): used by objdiff to read compiler output.', 'deep')
add('gimli-rs--gimli', ['re-binary-recon'], 'DWARF reader (Rust).')
add('icedland--iced', ['re-binary-recon'], 'Correct, fast x86/x64 decoder, formatter and assembler (Rust/.NET/Python/JS/Lua); instruction info API for register/memory/flow analysis.', 'deep')
add('nationalsecurityagency--ghidra', ['re-binary-recon','decomp-matching-workflow'], 'Reverse-engineering platform. Headless scripts (Decompile.java / Disassemble.java / bulk rename from symbols.txt) are how the Thief3 and AVP2 projects feed agents.')
add('memflow--memflow', ['re-binary-recon'], 'Out-of-process memory introspection for machines/VMs/dumps. Out of scope for these skills (no live-process tampering guidance).', 'deep')
add('frida--frida-rust', ['game-hooking-patterns'], 'Rust bindings to Frida (dynamic instrumentation).', 'deep')
add('hpmason--retour-rs', ['game-hooking-patterns'], 'Cross-platform inline detour library for Rust (trampolines, RIP-relative fixups, hot-patching); nightly needed for static_detour!.', 'deep')
add('jam1garner--binrw', ['game-asset-formats'], 'Declarative binary reader/writer macros: magic, endianness, padding, offsets (FilePtr), validation. Best-in-class for writing format parsers in Rust.', 'deep')
add('encounter--objdiff', ['decomp-matching-workflow'], 'The diff engine behind decomp.dev: compares compiled objects to target objects per symbol (x86/x64/PPC/MIPS/ARM/SH), `objdiff.json` units, report generation, WASM and CLI frontends.', 'deep')
add('simonlindholm--asm-differ', ['decomp-matching-workflow'], 'Python assembly differ used by decomp.me and many MIPS/PPC projects (`diff.py`, `diff_settings.py`).', 'deep')
for i, t in [('rust-lang--rust-bindgen','C header -> Rust FFI'),('dtolnay--cxx','safe Rust<->C++ bridge'),('google--autocxx','auto-generated Rust<->C++ binding'),('mozilla--cbindgen','Rust -> C/C++ headers'),('rust-lang--cc-rs','compile C/C++ from build.rs'),('nagisa--rust-libloading','dynamic library loading'),('mystor--rust-cpp','inline C++ in Rust')]:
    add(i, ['engine-reimplementation'], f'FFI tooling: {t}. Relevant when Rust code must talk to a C++ engine (OpenMW) or when exposing a Rust parser to C++.', 'meta')
for i, t in [('bevyengine--bevy','ECS game engine'),('fyroxengine--fyrox','game engine/editor'),('godot-rust--gdext','Godot bindings'),('gfx-rs--wgpu','graphics API'),('rust-sdl2--rust-sdl2','SDL2 bindings'),('dimforge--rapier','physics'),('dimforge--parry','collision'),('janhohenheim--rerecast','navmesh generation'),('gltf-rs--gltf','glTF loader'),('bitshifter--glam-rs','math'),('image-rs--image','image codecs'),('serde-rs--serde','serialization')]:
    add(i, ['engine-reimplementation'], f'Rust ecosystem building block: {t}. Candidate dependency for a clean-room port or tooling.', 'meta')
for i, t in [('proptest-rs--proptest','property-based tests'),('rust-fuzz--cargo-fuzz','fuzzing'),('model-checking--kani','model checking'),('nextest-rs--nextest','test runner'),('mitsuhiko--insta','snapshot tests'),('criterion-rs--criterion-rs','benchmarks')]:
    add(i, ['game-asset-formats'], f'Parser-hardening tool: {t}. Use for format libraries that read untrusted game files.', 'meta')

# ---- reimplementation / recompilation -----------------------------------------------------------
add('hedge-dev--unleashedrecomp', ['engine-reimplementation'], 'Static recompilation of an Xbox 360 game (PPC -> C++ via XenonRecomp, shaders via XenosRecomp) with a Windows/Linux runtime layer; assets always user-supplied through an installer.', 'deep')
add('sonicnext-dev--marathonrecomp', ['engine-reimplementation'], 'Second XenonRecomp-based port; shows how the toolchain generalises across games.', 'readme')
add('alexbatalov--fallout1-ce', ['engine-reimplementation'], 'Playable reimplementation of Fallout 1 with bug fixes and QoL; drop-in replacement executable using the user\'s data files, SDL2 portability.', 'readme')
add('alexbatalov--fallout2-ce', ['engine-reimplementation'], 'Same approach for Fallout 2.', 'readme')
add('diasurgical--devilution', ['engine-reimplementation'], 'Reconstructed Diablo 1 source: names/structure came from debug symbols that leaked on a console port (Japanese PSX build), then verified against the PC binary with a function comparer.', 'readme')
add('id-software--doom-3-bfg', ['engine-reimplementation'], 'Official id Software source release of DOOM 3 BFG Edition (GPL-3.0); MSVC build; reference architecture for a modern id Tech 4 engine.', 'meta')
add('open-goal--jak-project', ['engine-reimplementation','decomp-matching-workflow'], 'Decompiler + compiler for a custom Lisp (GOAL) + C++ runtime: an end-to-end port strategy (extract assets -> decompile -> recompile natively -> runtime). AGENTS.md: disclose AI use "(AI-assisted)"; never open issues or PRs on the user\'s behalf.', 'deep', 'disclose')
add('nicoruedaa--project-arceus', ['engine-reimplementation'], 'Rust/Bevy port driven by a versioned "spreadsheet book" of reverse-engineered facts (the Spreadsheet Method).', 'readme')
for i in ('pret--pokered','pret--pokegold','pret--pokecrystal','pret--pokeruby','pret--pokeheartgold'):
    add(i, ['decomp-matching-workflow'], 'pret disassembly project: assembly-first (disassemble, label, then lift to C) with byte-for-byte rebuild as the correctness test.', 'meta')

# ---- decomp exemplars ----------------------------------------------------------------------------
add('veradictus--thief3-decomp', ['decomp-matching-workflow','game-hooking-patterns'], 'MSVC 7.1 x86 matching decomp driven by Claude workers: claim queue, context packets, try/accept gate with rulers, deferral slugs, family stamping, CHEATSHEET of verified codegen idioms, headless-Ghidra scripts, SDK mod loader (dinput8 proxy, MinHook/IAT hooks, PE-timestamp guard). Best agent-workflow reference. MIT.', 'deep', 'ai-ok')
add('openblack--bw1-decomp', ['decomp-matching-workflow'], 'MSVC6 x86 matching decomp with dtk+objdiff; AGENTS.md has the best "mindset" and experiment-discipline guidance (classify the diff, prove a knob moves output, bound the search), baseline/regression tooling, inline-budget analysis, Mac CodeWarrior symbols as ground truth. CC0.', 'deep', 'ai-ok')
add('lemiur--avp2-reconstructed', ['decomp-matching-workflow','re-binary-recon'], 'LithTech engine, VC6 SP5: 92% byte-matched with reccmp-style annotations, objdiff reports, relink verification, library-code identification, behaviour audit of STUB functions, Ghidra name sync, second module (renderer DLL) with a different compiler.', 'deep', 'ai-ok')
add('marijnvdwerf--legoland', ['decomp-matching-workflow'], 'MSVC6 matching decomp using reccmp + wibo on Linux; CLAUDE.md shows a compact agent brief (no inline asm, no goto, STUB macro, CRT/imports stay stubs).', 'deep', 'ai-ok')
add('isledecomp--isle', ['decomp-matching-workflow'], 'Reference x86 MSVC project: reccmp annotations (// FUNCTION/STUB/GLOBAL/VTABLE), reccmp-project.yml targets with sha256, ReproBit byte-for-byte verification, beta/debug builds as ground truth, Kaitai format docs. LGPL-3.0.', 'deep')
add('punpckhdq--halo', ['halo-engine-re','decomp-matching-workflow'], 'Halo CE (build 2342, Xbox cachebeta.exe): ninja configure.py, Xbox SDK compiler, types borrowed from later debug builds via pdb-decompiler, bungie-style source tree (ai, objects, units, tag_files, hs scripting, rasterizer...). CC0. 15% code.', 'deep')
add('chimpsatsea--reach', ['halo-engine-re'], 'Halo Reach (Xbox 360) decomp: ninja configure.py, GPL-3.0, <1% so far; same engine lineage as Halo CE.', 'readme')
add('ieee802dot11ac--fnv', ['bethesda-gamebryo-re'], 'Fallout: New Vegas Xbox 360 MemDebug build: reconstructed Gamebryo 2.2 and Bethesda TES* class headers. Policy: asks contributors not to use AI to decompile; used here for structure orientation only.', 'deep', 'human-only')
add('dbalatoni13--nfsmw', ['decomp-matching-workflow'], 'NFS Most Wanted multi-platform decomp; "SAY NO TO SLOP" policy (LLM only for rough passes/tooling with manual review). CC0.', 'readme', 'ai-ok')
add('banteg--crimson', ['decomp-matching-workflow'], 'Crimsonland 1.9.93 (2003, GOG Classic) rebuilt twice per README; Python tooling, MSVC; ~64%.', 'readme')
add('bluisblu--pvz', ['decomp-matching-workflow'], 'PvZ 0.9.9 beta build: MSVC via wibo, ninja configure.py + objdiff; <1% so far.', 'readme')
add('emoluvjd2--oregontrail-win32-decomp', ['decomp-matching-workflow'], 'Reconstructed C++ for Oregon32.exe/OREGON32.DLL (1996): MSVC, Ghidra + objdiff, ~56%.', 'readme')
add('haydntrigg--homeworld2classic', ['decomp-matching-workflow'], 'Homeworld 2 decomp (Windows): objdiff + decomp.dev + ninja-style config/; ~4%.', 'readme')
add('rsdkmodding--sonic-mania-decompilation', ['engine-reimplementation'], 'RSDK-engine game-logic decompilation as a portable, mod-friendly native port (not byte-matching); needs the original assets.', 'readme')
add('pakompom--spacerangers1-decomp', ['decomp-matching-workflow'], 'Recovers the original DELPHI source (not C/C++) for Space Rangers 1/HD; cargo tooling; reported 100%. Example of a non-MSVC target.', 'readme')
add('xeeynamo--sotn-decomp', ['decomp-matching-workflow'], 'SotN decomp for PS1 (also PSP and Saturn): maspsx, splat, asm-differ, decomp-permuter, m2c, Ghidra/IDA in the workflow; AGPL-3.0; ~69%.', 'readme')
add('zeldaret--oot', ['decomp-matching-workflow'], 'OoT (N64): IDO and GCC toolchains per README, docker + make/python build, SHA-1 verification; reported 100% while the README still calls the repo work in progress.', 'meta')
add('doldecomp--melee', ['decomp-matching-workflow'], 'Matching decomp of Melee (US, GameCube): MWCC run under wibo/wine, ninja configure.py, objdiff + decomp.dev reports, m2c; reported 100%. Canonical GC/Wii workflow (see decompedia guide).', 'readme')
add('zeldaret--botw', ['decomp-matching-workflow'], 'Experimental WIP decompilation of BotW v1.5.0 (Switch); cmake build; catalog notes it is not a playable standalone port.', 'meta')
add('almamu--crashbandicootxs-decomp', ['decomp-matching-workflow'], 'GBA decomp with an explicit "AI-assisted decompilation" section: nothing trusted on the AI\'s say-so; every function verified.', 'readme', 'ai-ok')

# ---- AI policy flags (from READMEs; always re-read CONTRIBUTING before contributing) -------------
for i in ('2tie--mh1j',):
    add(i, ['gamedecomp-library'], 'README forbids AI-produced code AND indexing/modification of the repo by agents. Do not ingest or contribute.', 'readme', 'human-only')
for i in ('theplayerrolo--lm-decomp','xbret--xenoblade','ryan-myers--jet-force-gemini','synamaxmusic--bar-decomp','shdecompilations--silent-hill-decomp','bluisblu--cttr'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'human-only'
for i in ('zeldaret--tww','doldecomp--ogws','smgcommunity--petari','smgcommunity--garigari','nsmbw-community--nsmbw-decomp'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'no-ai-decomp'
for i in ('ashfordfamily--recvx-decomp',):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'disclose'
for i in ('cosmicscribe64--eds-decomp','jovinull--sonicheroes','lifewillbeokay--moh-rising-sun','mateuszklysz--lombyte','melalawi--battletanx-decomp','melalawi--ragewars-decomp','opokxeno--xsg-i-decomp','denzi-gh--crashwoc-decomp-gc','gaberealb--parasite-eve-2-decomp','laqieer--fireemblem8j','shibbo--3dwdecomp','pattytrish--unending-occlusion','cdlewis--snowboardkids2-decomp','dimforge--rapier'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i].setdefault('ai', 'ai-ok')

# ---- sources and later additions ------------------------------------------------------------------
add('rehan-remade--universal-modder', ['gamedecomp-library','game-hooking-patterns','bethesda-gamebryo-re'], 'MIT. Agent-first modding toolkit: 10 skills (mod-any-game loop, game-recon, reverse-engineering, mashup-mods...), 12 engine playbooks (incl. Bethesda, native, retro decomp), the `um` CLI (scan, kb, backup, publish check) and a knowledge base of ~59 agent-written field notes with symptom->cause->fix gotchas and a public index.json. Snapshotted into this hub (field-notes.json, playbooks.json).', 'deep', 'ai-ok')
add('samidyfr--game-decompilations', ['gamedecomp-library'], 'Alphabetical list of ~670 game decompilation repos (credits awesome-game-decomps, RetroReversing, decomp.dev); source of ~480 extra catalog entries here.', 'readme')
add('decompals--decompedia', ['decomp-matching-workflow'], 'Decomp wiki export: intro to the decomp process, MWCC/GCC/IDO compiler pages, platform pages, assembly patterns, $gp register, line numbers, maspsx, decomp.dev integration guide, per-project pages. No licence file: paraphrase only.', 'deep')
add('solarfren69420--gamedecomplibrary', ['gamedecomp-library'], 'Catalog of 304 projects with progress snapshots, methods and evidence links; its site catalog.json is the primary data source here.', 'deep')
for i in ('ryan-myers--jet-force-gemini','2tie--mh1j','shdecompilations--silent-hill-decomp','xbret--xenoblade','synamaxmusic--bar-decomp','atenfyr--uassetapi','blackgamma7--aidyn','novapowers0--bloodyroar2recomp','twist84--halo3_cache_release_recomp','vatuu--silent-hill-decomp','sat-r--sa2','sat-r--sa3','zelda64recomp--zelda64recomp','solarcookies--tip-recomp','theplayerrolo--lm-decomp','bluisblu--cttr','ieee802dot11ac--fnv'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'human-only'
for i in ('nsmbw-community--nsmbw-decomp','smgcommunity--garigari','smgcommunity--petari','zeldaret--tww','doldecomp--ogws'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'no-ai-decomp'
for i in ('fmil95--recvx-decomp','ashfordfamily--recvx-decomp'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'disclose'
for i in ('gerev--bumpy-reverse','pattytrish--unending-occlusion','lifewillbeokay--moh-rising-sun'):
    O.setdefault(i, {'use': [], 'note': '', 'depth': 'readme'}); O[i]['ai'] = 'ai-ok'
json.dump(O, open(sys.argv[1] if len(sys.argv) > 1 else 'overlay.json', 'w'), indent=1, sort_keys=True)
print(len(O), 'overlay entries')

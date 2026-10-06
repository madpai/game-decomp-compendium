---
name: engine-reimplementation
description: Strategies and patterns for turning a shipped game into something that runs on new platforms or with new capabilities: matching decompilation to source ports, static recompilation (PPC/MIPS/N64/Xbox 360 to C++), clean-room engine reimplementations that read the user's own data (Fallout CE, Devilution, OpenMW-style), patched donor engines (OpenOblivion on OpenMW), decomp-as-library, headless-rules reimplementation, Android/mobile ports. Use when planning or reviewing a port, remake, "open engine", recompilation or preservation project, choosing between approaches, designing asset handling (installer wizards, private caches), verification oracles, upstream-patch carrying, or licensing posture for such a project.
---

# Engine reimplementation and porting strategies

First ask what the user needs, because approaches differ by an order of magnitude in effort:

| Approach | What you produce | Effort | Fidelity oracle | Exemplars (see catalog) |
|---|---|---|---|---|
| **Matching decomp -> source port** | source that rebuilds the original bytes, then a platform layer | very high | byte equality of objects/executable | OoT/SM64 ports, Melee, Halo CE decomp, Thief 3 SDK, isle |
| **Static recompilation** | original machine code translated to C++ plus a runtime reimplementing the console/OS | high tooling, low per-game | runs the original code; compare traces/frames | N64Recomp, XenonRecomp/UnleashedRecomp/MarathonRecomp, PS2Recomp |
| **Clean-room reimplementation reading user's data** | new engine, same rules, uses original data files | high | behaviour tests against the original game/data, recomp as oracle | Fallout 1/2 CE, Devilution (reconstructed source), OpenMW, IW4L-style rewrites |
| **Patched donor engine** | existing open engine plus reproducible patches and a data/script translation layer | medium | real-data assertions + visual probes | OpenOblivion (OpenMW donor) |
| **Decomp/recomp as library** | the game logic embedded in another host | medium | library API tests + host integration | libsm64 |
| **Headless rules sim + host as view** | pure simulation of guest rules, host renders | medium | headless bench + scripted real-world run | Bloons TD 6 inside Minecraft |
Search `hub.py prior-art "<game>"` for existing decomps/recomps first: reusing one is cheaper than starting.

## Cross-cutting rules (all approaches)
1. **User supplies the assets and binary.** Installer/wizard that accepts the user's dumps (Unleashed Recomp validates and extracts), or a converter that writes a *private* cache on the user's machine/device. Never ship assets, extracted data, or tables derived from the executable; keep generated data out of git and behind `.gitignore`.
2. **One oracle per claim**, chosen before coding: byte match, trace replay, real-data assertion over all records, screenshot diff, headless bench. Automate the loop. See `re-binary-recon/references/rtti-vtables-and-oracles.md`.
3. **Status honesty**: a rule table with *verified / documented / inferred / guessed* per behaviour (OpenOblivion's table is a template); unimplemented features return a documented default and log once.
4. **Reproducibility**: pin donor/upstream revisions; carry changes as hash-locked "receipts" (script + lock file + per-platform patches + tests) so any native change can be regenerated and audited (OpenOblivion `tools/native/*`).
5. **Keep original behaviour first**, including bugs, then offer fixes behind switches (Devilution keeps original quirks; Fallout CE adds bugfixes and QoL as a separate layer).
6. **Scope control**: vertical slice (one quest/level/room end to end) before breadth; version tags per slice; screenshot per feature.
7. **Legal posture**: source-only repos, CC0/permissive for original work, upstream licences honoured (GPL donors keep GPL), no leaked material, credit sources; some communities ban AI contributions: check policies (`hub.py` shows `ai`). See `decomp-matching-workflow/references/legal-and-etiquette.md`.

## Pattern notes by approach
**Source ports from decomps** (jak-project, OoT, Melee): four components recur: (1) extractor/decompiler for the user's media, (2) compiler or build for the recovered source, (3) game source, (4) a runtime layer that reimplements hardware/OS services (jak: C kernel + linker, Sony library shims, IOP driver, sound library, OpenGL renderer). jak-project also keeps a REPL/debugger connection to the running game (live edit), cross-platform task automation (`task`), and an `AGENTS.md` (disclose AI use; never open issues/PRs).

**Static recompilation** (UnleashedRecomp): inputs are the user's `default.xex` + title update (`.xexp`) + shader archive; PPC code is translated to C++ by XenonRecomp and Xenos shaders to HLSL by XenosRecomp, then compiled with clang/VS2022 + CMake; a runtime layer supplies kernel/GPU/audio/input; an installer wizard dumps and validates content (retail disc or digital copy, DLC optional); improvements (resolution, frame rate, ultrawide) are layered on top. Hardware needs (AVX, D3D12/Vulkan) are stated up front. Windows and Linux builds from one tree.

**Clean-room reimplementation** (Fallout CE, Devilution): drop-in replacement executable that reads the original data files; SDL2 for portability; compatibility matrix and debug features documented; Devilution derived names/structure from symbols that leaked on a console port, then verified against the PC binary with a function comparer (`comparer-config/*.toml`) and compiles with the original VC6 (SP5 + Processor Pack "important for proper code generation") as well as modern toolchains (DEP must be disabled for a DLL that generates code at runtime).

**Patched donor engine** (OpenOblivion on OpenMW): choose a donor whose subsystems already fit (rendering, UI, Lua API, input). Add a translation layer for the new game's data (script compiler to the donor's scripting language, dialogue/quest runtime in Lua), keep private generated data out of the repo, ship overlay scripts in the app package, build a desktop probe (headless render + scripted UI clicks) so features can be verified without a phone. Mobile specifics that bit: touch overlay for GUI mode, BACK button must close any menu, big tap targets, tap logging to separate "never arrived" from "did nothing", GameActivity back handling, keep APK size/gradle and native receipts reproducible, publish versioned test builds with release notes.

**Decomp as library** (libsm64): expose collision/input in, state/mesh out; host feeds its geometry; user supplies the ROM.

**Headless rules sim** (BTD6-in-Minecraft): simulation at the guest's own step rate and units; one frame-mapping function; mirror entities only where the player must touch; batch records for high-volume objects; every UI button is a command; host features feed the sim, never bypass it; placeholders when the private asset pack is missing.

## Android/mobile porting checklist (from OpenOblivion and Halo Android work)
Native libs via NDK/CMake with a pinned donor; SDL activity lifecycle; touch controls with a visible menu exit; asset import flow (user-provided data folder or on-device conversion); performance probes (draw calls, triangle counts: a 1.2M-triangle map was heavy on a phone); logs viewable in-app; backups of generated caches; test on the device early because desktop probes miss touch and GPU limits.

## Files
- `references/approach-selection.md`: decision questions, cost drivers, risks, and a worked comparison for an Oblivion-class RPG and for a small 2D game.

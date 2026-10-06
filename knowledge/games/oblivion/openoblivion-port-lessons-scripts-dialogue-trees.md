---
kind: game
title: "OpenOblivion lessons: TES4 script compiler, dialogue/quest runtime, SpeedTree billboards and touch menus on a patched OpenMW"
game: "The Elder Scrolls IV: Oblivion"
games_also: []
game_version: "OpenOblivion builds 0.40-0.44 on a patched OpenMW (desktop pin vs Android donor, Lua API rev 160 vs 129); Oblivion.esm from a retail install"
platform: windows
engine: gamebryo
route: reimplementation
tools: ["OpenMW (patched)", "LuaJIT", "docker probe image with xdotool", "tes4_script.py compiler", "ctest fixtures"]
anti_cheat: "none (single-player port; owner's own data)"
status: in-progress
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-05
links: ["https://github.com/madpai/OpenOblivion"]
tags: [openmw, lua, scripting, dialogue, quests, speedtree, android, touch-ui]
---

# OpenOblivion lessons: scripts, dialogue, trees, touch menus

> What a 1:1 Android port of Oblivion on a patched OpenMW needed for trees, quests/journal, spoken conversations, object scripts and always-closable menus, with the bugs that cost time. Verified on desktop probes and CI; phone confirmation of 0.40-0.44 was pending when written.

## Setup
OpenMW pinned twice (desktop pin and Android donor); native changes as hash-locked receipts (script + lock + per-platform patches + tests); overlay Lua in the APK; private data generated from the owner's install (never committed); desktop probe tool renders scenes and drives UI clicks (docker image plus xdotool).

## Route and why
Donor engine plus translation layers: ESM/BSA/NIF are documented, scripts keep their source text beside the bytecode, dialogue and quests are data-driven. Script source is compiled to Lua using the parameter lists of the command table read from the exe; a runtime in Lua runs result scripts, conditions, quests and dialogue.

## How the game works (rules and their status)
Responses of a topic are tried in file order, first passing wins (documented); random and say-once flags (documented); topic list rule is an inference; `GetInCell` of a dummy cell is approximated by the city worldspace or exterior cells within two of the map marker; `SetStage` starts a non-running quest (inferred); `OnActivate` replaces the default activation unless the script calls `Activate`, with fail-open fallback; conditions: CTDA function number is opcode minus 0x1000; OR groups join with the next condition and a trailing OR stays open. Voices: `sound/voice/oblivion.esm/<race>/<m|f>/<quest>_<topic>_<info8hex>_<n>.mp3`.

## Verification
Compiler statement-level opcode sequence equals the bytecode's for all 7,945 scripts with both source and bytecode (two differ: their source lacks an End/Endif); fixtures for compiler, runtime and dialogue run in CTest; end-to-end on the real master with a mock world (starting a new game chains quest stages with journal text); desktop probes screenshot the conversation window and journal. **Not verified**: phone behaviour of 0.40-0.44, voice playback audibility, trunk collision, rule guesses above.

## Gotchas
1. **Generated Lua was invalid for unclosed or stray `If/Else/Endif`.** **Cause:** scripts whose source lacks an End/Endif. **Fix:** stack-guard blocks with `[kind, else_seen]` and close implicitly.
2. **Dialogue condition groups misbehaved at the end of a list.** **Cause:** trailing OR. **Fix:** an explicit `open` flag on the group.
3. **FormIDs did not match across files.** **Cause:** load-order byte in the high byte. **Fix:** `% 0x1000000` before comparing.
4. **Command parameter types mismatched at compile time.** **Cause:** a second, hand-written table disagreed with the extractor's output. **Fix:** use the committed extractor output only.
5. **Android build error returning a shared_ptr where an `osg::ref_ptr` was expected.** **Fix:** `return {};` in the patch.
6. **Desktop probe lost overlay scripts when positioning the player.** **Cause:** the start-position script teleported. **Fix:** skip the teleport when a start-override module is present.
7. **Probe screenshots taken before the UI existed.** **Fix:** guard on `not config.ui` timing.
8. **xdotool clicks failed in the probe container.** **Cause:** missing `XAUTHORITY`. **Fix:** set it; poll container logs instead of waiting for a stdout file written at the end.
9. **Phone user could not close the journal.** **Cause:** unconfirmed (22 px "Close" text easy to miss on touch). **Fix/mitigation:** BACK button in the touch overlay while any menu is open (sends Escape), Android back key closes menus first, big Close/Goodbye buttons, tap on any unused part of the page closes it, and `OPENOBLIVION_UI tap` logging to separate "tap never arrived" from "tap did nothing".
10. **A patch script clobbered pristine copies.** **Fix:** generate patches from `trees/KIND/a` copies, never overwrite the pristines.
11. **Trees invisible.** **Cause:** OpenMW ignores `.spt` SpeedTree files. **Fix:** a `tes4_trees` receipt turns `.spt` into two crossed billboard quads sized from the TREE record's billboard width/height, with `simpleLighting`; pitfall: `SceneUtil::Material` versus `osg::Material` differ between pins.

## Open questions
Quest-script delay value and topic-list rule (see `oblivion-exe-recon-rtti-voices-gmst.md`), barter/persuasion/magic menus, creature bridge, trunk collision, grass.

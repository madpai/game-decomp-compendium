---
kind: game
title: "Oblivion's UI is data (menu XML in Misc.bsa) and how to measure script-command coverage by call sites"
game: "The Elder Scrolls IV: Oblivion"
games_also: []
game_version: "Steam retail install; Oblivion.esm and Oblivion - Misc.bsa from the same install"
platform: windows
engine: gamebryo
route: reimplementation
tools: ["bsa reader (own, ~40 lines)", "script compiler to Lua", "regex over generated code", "re-binary-recon/string_xrefs.py"]
anti_cheat: "None involved: files read from disk only"
status: working
agents: ["Claude Code (Sonnet 5.5)"]
humans: []
date: 2026-10-06
links: ["https://github.com/madpai/OpenOblivion/blob/main/docs/REVIEW_AND_PLAN.md"]
tags: [ui, menus, xml, scripting, coverage, planning, openmw, port]
---

# Oblivion's UI is data, and how to measure script-command coverage

> Two measurements that change how a port should be planned: the original menus are 104 XML files (an expression language over DDS art), so UI parity means writing an interpreter, not hand-building screens; and counting command call sites in the compiled master shows which subsystems (not which commands) the script runtime is missing.

## Setup
Retail `Oblivion - Misc.bsa` (BSA v103) and `Oblivion.esm`; a script-to-Lua compiler that resolves commands from the executable's command table; Python 3 only.

## Route and why
Measure before building: list what the original ships as data, and quantify how much of the real script surface a runtime covers, so the next implementation step is chosen from data rather than from the last bug report.

## How the game works (what we learned)
- `Oblivion - Misc.bsa` holds 104 files under `menus\` (115 files in all with fonts): `negotiate_menu.xml` (barter), `persuasion_menu.xml`, `lockpick_menu.xml`, `container_menu.xml`, `levelup_menu.xml`, `book_menu.xml`, `training_menu.xml`, `message_menu.xml`, plus `strings.xml`, `menu_labels.txt`, `master_menu_file.txt` and a `prefabs\` folder.
- The XML is a declarative layout language: nested `rect`/`image`/`text` tiles with *traits* whose values are expression trees (`copy src= trait=`, `ref`, `include`, `add`, `sub`, `mul`, `div`, `eq`, `onlyif`, `onlyifnot`), entity macros (`&true;`, `&center;`), per-tile user variables (`user0..N`) and handlers (`clicked`, `xup`, `xdown`). 1.22 MB in total, 570 distinct tag names, but about 40 tags make up almost all of it.
- The executable has `Tile`, `TileMenu`, `TileRect` and ~38 `*Menu` classes (RTTI): the C++ menu classes fill user traits from game state; layout and art are data.
- Script command coverage: compile every script and fragment, then count `C.name(` call sites in the generated Lua. In the project measured, 65 implemented commands covered 65.9% of 32,677 call sites (251 distinct commands used); the 195 missing commands (11,141 sites) bucket into AI packages (~23%), magic (~15%), animation groups (~13%), speech and sound (~11%), combat (~11%), world/object state (~9%) and actor values (~8%).
- `fQuestScriptDelayTime` is an INI setting whose shipped default (5.0) lives in `Oblivion_default.ini`; there is no object-script delay setting.

## Build steps
1. List `menus\*.xml` from the BSA (any v103 reader) and count tags with a regex.
2. Generate the script data with the compiler, then `grep -ohE '\bC\.[a-z0-9_]+\(' ... | sort | uniq -c`; subtract the names the runtime defines (`function C.name`, `C.a, C.b = ...`).
3. Bucket the missing names by subsystem with a regex table; rank by call sites.

## Verification
Counts are exact for the compiled data; the subsystem buckets are regex-based and approximate (about 1,000 sites stayed unbucketed). Not verified: that every menu is expressible by an interpreter of the common tags (a long tail of 500+ tags exists), runtime behaviour of the original menus.

## Gotchas
1. **Command coverage by distinct names looks small.** **Cause:** the long tail of rare commands. **Fix:** weigh by call sites and group by subsystem; five subsystems explain most of the gap.
2. **A missing command that returns a value is not a harmless stub.** **Cause:** the runtime returns 0 and logs once, so conditions silently take the wrong branch. **Fix:** count value-returning stubs separately and make them loud.
3. **Regex bucketing misfiles commands.** **Fix:** treat percentages as approximate; fix the bucket table when reviewing the top 50.
4. **Menu XML invites hand-translation.** **Cause:** each screen is small. **Fix:** write the expression/tile interpreter once; per-menu code should only supply user-trait values.
5. **Setting not found among game settings.** **Cause:** it is an INI setting (name carries a `:Section` suffix in the executable) with its default in the shipped INI file. **Fix:** look in `Oblivion_default.ini` and for `name:Section` strings.

## Open questions
How user traits are updated per frame; which menus need native widgets (map, inventory 3D preview); whether `clicked` handlers imply a script-like VM in the tile system.

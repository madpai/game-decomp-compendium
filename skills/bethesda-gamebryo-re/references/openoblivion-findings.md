# OpenOblivion: decisions and findings worth reusing

OpenOblivion (github.com/madpai/OpenOblivion) is a 1:1 port of Oblivion for Android built on a patched OpenMW. These notes summarise its public research docs (`docs/research/*`, `docs/HANDOFF.md`) plus what the executable/data checks above added. Never commit game data or exe-derived tables; everything generated from the owner's install stays private and is rebuilt on-device or locally.

## Architecture in one paragraph
OpenMW is the engine; the port patches it with hash-locked "receipts" (a Python script + lock file + desktop patch + Android patch, e.g. `tes4_trees.py`, `tes4_trees_{desktop,android}.patch`) so every native change is reproducible against two pinned OpenMW revisions (desktop pin vs Android donor, Lua API rev 160 vs 129). Overlay Lua scripts ship in the APK; private generated data (`scripts/tes4data/*.lua`, converted assets) is built from the owner's Oblivion install and never committed. A desktop probe tool (`probe_scene.py`, docker image with OpenMW, xdotool for UI clicks) renders scenes and exercises UI flows headlessly; CI runs a `foundation` workflow and CTest suites (script compiler fixtures, runtime fixtures, dialogue fixtures).

## Script/quest/dialogue stack (what exists)
`tes4_commands.py` reads the command table from the exe -> `tes4_script.py` compiles SCTX source to Lua with exact parameter lists (identifiers resolved to FormIDs at compile time; unknown trailing words ignored like the original) -> `tes4_gamedata.py` writes private overlay data (quests, index, actors, result-script fragments 128/file, object/quest scripts 32/file, dialogue) -> runtime Lua (`openoblivion_tes4_script/commands/dialogue/game/ui`) runs it. Object scripts attach to placed references (3,042 base records carry scripts); `OnActivate` replaces default activation unless the script calls `Activate`, with fail-open fallback so a script bug never locks an object.

## Rule status table (keep this honest)
| Rule | Status |
|---|---|
| Responses tried in file order; first passing wins | documented, not compared with exe |
| Random flag, say-once | documented |
| Topic list rule (type "topic", learned via AddTopic, never if only a choice) | **inference** |
| `GetInCell` of a dummy cell = city worldspace or exterior cells within 2 of the map marker | **approximation** |
| `SetStage` starts a non-running quest | inferred |
| Quest scripts run every 5 s | the original's delay is a game setting, not yet read |
| Voice file name `<quest>_<topic>_<info8hex>_<n>.mp3` under `sound/voice/oblivion.esm/<race>/<m|f>/` | **verified** (archive contents, bsa-rs example, exe format string `%s_%s_%08X_%u`) |
| Unimplemented commands return 0 and are logged once | choice (some conditions pass wrongly) |

## Next verification targets (cheap with the recon scripts)
1. Read the quest-script delay setting and topic-list construction by following the `TESTopic`/`TopicInfoArray`/`DialogMenu` classes from RTTI (`rtti_scan.py --grep "Topic|Dialog"`, then string pivots).
2. Lip-sync (`.lip`) files and the emotion list (Surprise, Happy, Sad, Fear, Disgust, Anger, Neutral) next to the voice strings: facial animation channel for conversations.
3. Barter (`NegotiateMenu`), persuasion (`PersuasionMenu`), lockpicking, alchemy, enchantment, level-up and race/sex menus exist as classes: a menu roadmap.
4. Trees: `BSTreeNode` and the `SpeedTree*` shader properties define how branches/fronds/leaves are lit; compare with the billboard approximation.

## Practices that worked
Version tags per feature (`0.41-quests` ... `0.44-menu-exit`), a probe screenshot per feature, receipts for every native patch, tap logging in UI (`OPENOBLIVION_UI tap ...`) so a phone report can distinguish "tap never arrived" from "tap did nothing", a BACK button and big Close/Goodbye buttons because menus must always be exit-able on touch, `GameActivity.onBackPressed` closing menus first.

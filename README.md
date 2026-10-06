# Game Decomp Compendium

Institutional memory **for AI agents** (and the humans directing them) working on game reverse engineering, decompilation, modding, porting and asset extraction. It combines a searchable dataset of ~790 decompilation and RE-tool projects, agent-written field notes with their gotchas, **structured experiment and dead-end records**, evidence-tagged **findings**, a small typed **research graph** (games, engines, physics middleware, techniques, projects, formats, problems), engine playbooks, and eight installable skills with tested scripts. The measure of success is how often an agent solves a new technical problem *without rediscovering something already learned*, not how many projects are indexed.

> **If you are an AI agent:** read [`AGENTS.md`](AGENTS.md), then `skills/gamedecomp-library/SKILL.md`, then run
> `python3 skills/gamedecomp-library/scripts/hub.py prior-art "<game or engine>"`.
> Symptom first? `hub.py diagnose "<symptom>"`. About to try something? `hub.py tried "<idea>"`.
> You do not need to read this whole repository: the tools return pointers to the few files that matter.

## What is inside

| Skill (`skills/<name>`) | Use it for |
|---|---|
| **gamedecomp-library** | Entry point. Searchable data (`hub.py`: `prior-art`, `diagnose`, `tried`, `graph`, `search`; `query.py`), research graph, experiments and findings, golden-query tests, agent operating manual, project feedback loop, refresh and clone tooling |
| **decomp-matching-workflow** | Matching decompilation: toolchain map (objdiff, dtk, splat, reccmp, asm-differ), per-function loop, experiment discipline, running many agents (claim queue, gates, sweeps), compiler idioms (MSVC/MWCC/GCC/IDO), legal posture |
| **re-binary-recon** | Static recon of Windows exes/DLLs: triage, **MSVC RTTI class/vtable recovery**, string-to-function pivots, AOB signatures. Pure-Python scripts tested on x86 and x64 binaries |
| **game-hooking-patterns** | Offline/single-player runtime modding: loaders per engine, proxy DLLs, hooks, signature/RTTI resolution, fromsoftware-rs patterns, hard safety rules |
| **bethesda-gamebryo-re** | Oblivion/Gamebryo: ESM/ESP/BSA formats, script bytecode, CTDA/dialogue/quests, voice naming, engine class map, **Havok/Gamebryo physics** (bhk* collision, MOPP, tri-strips, layers, the player controller hull, stairs, translating to Bullet), OpenOblivion findings (with evidence levels) |
| **halo-engine-re** | Halo tags and caches, Halo CE decomp module map, Halo 3 MCC reading notes |
| **engine-reimplementation** | Ports and remakes: decomp-to-port, static recompilation, clean-room engines, patched donor engines, Android checklist, approach selection |
| **game-asset-formats** | Identify unknown files (`identify.py`), reverse-engineer formats with round-trip oracles, Source MDL/VTF/VPK, parser safety, per-engine tool table |

Data (in `skills/gamedecomp-library/data/`):
- `catalog.json` / `catalog.tsv`: 790 projects (702 decomps, 72 tools, 15 related, 1 unconfirmed) with platform, type, compilers/tools/build styles, progress, licence, stars, push date, read-depth, AI-contribution policy flag, notes.
- `field-notes.json`: 59 agent-written field notes from [universal-modder](https://github.com/rehan-remade/universal-modder) (50 games, 9 techniques, ~680 symptom→cause→fix gotchas), `playbooks.json` (12 engine playbooks), `modder-skills.json`.
- `local-notes.json`: this repository's own field notes (`knowledge/`: Oblivion exe recon, menu XML and script-command coverage, static-recon technique, OpenOblivion lessons and the movement/collision case study, Android emulator testing of arm64 ports, adb over Tailscale, reviewing an in-flight port; same format as universal-modder's, so they can be offered upstream), with every numbered gotcha parsed into symptom / cause / fix. `modder-gotchas.json` adds short extracts of the 684 upstream gotchas.
- `graph.json`: the research graph (about 90 nodes, 125 hand-written edges, 23 findings, 15 experiments) generated from `knowledge/graph/*.jsonl` and `knowledge/experiments/*.md`. Every edge, finding and experiment carries an evidence level (guessed < inferred < documented < static < verified) and a source pointer that resolves; findings carry a scope (build / project / family) so one project's choice never becomes an engine fact. `experiments.json` holds the structured experiment and dead-end records (failed ones are first-class). Schema and rules: `skills/gamedecomp-library/references/research-graph.md`.
- `sources.json`: where everything came from, licences, snapshot dates, refresh commands.

## Quick start

```bash
git clone https://github.com/madpai/game-decomp-compendium.git
cd game-decomp-compendium
./install.sh                    # copies the skills into ~/.claude/skills (any agent that reads SKILL.md folders can use them)

python3 skills/gamedecomp-library/scripts/hub.py prior-art "oblivion"
python3 skills/gamedecomp-library/scripts/hub.py diagnose "player shakes while walking upstairs"   # symptom -> subsystems, incidents, causes, oracles, failed approaches
python3 skills/gamedecomp-library/scripts/hub.py tried "lua onFrame camera smoothing"            # was this tried? did it fail, and why?
python3 skills/gamedecomp-library/scripts/hub.py graph find project --has msvc --has havok --has gamebryo --rel reverse_engineered:movement
python3 skills/gamedecomp-library/scripts/hub.py search "inline budget tie-break" --source refs
python3 skills/gamedecomp-library/scripts/query.py --platform Windows --compiler MSVC --min-progress 50
python3 skills/re-binary-recon/scripts/rtti_scan.py /path/to/game.exe --grep "Actor|Quest"
python3 skills/game-asset-formats/scripts/identify.py "/path/to/game/Data" --summary
```
No clone needed to *query*: if the data folder is absent, the tools download it from this repository into `~/.cache/gamedecomp-compendium/`.
You can also point an agent at the raw files, e.g. `https://raw.githubusercontent.com/madpai/game-decomp-compendium/main/skills/gamedecomp-library/data/catalog.tsv`.

## The feedback loop
```
Compendium -> active project -> new discovery / failed experiment / technique -> experiment, finding or field note -> Compendium -> future projects
```
Projects query before researching and write back when they finish: every failed or partial attempt becomes an experiment record, every reusable measured fact a finding, every trap a field note. The compendium is a research dependency, never a runtime one. Paste-ready instructions for OpenOblivion, MegaMod Showdown, Open Asset Lab or any future decomp/reimplementation repo: `hub.py snippet` (source: [`project-integration.md`](skills/gamedecomp-library/references/project-integration.md)).

## Ground rules baked into every skill
Own copy of the game only; offline/single-player for runtime work; no anti-cheat or DRM bypass; no game files, assets, decompiler dumps or executable-derived tables in repositories; respect each project's AI-contribution policy (the catalog flags it); never open issues/PRs on someone's behalf unasked; evidence levels on every fact; an oracle for every claim. Details: `skills/decomp-matching-workflow/references/legal-and-etiquette.md`, `skills/game-hooking-patterns/references/safety-and-etiquette.md`.

## Keeping it current
`skills/gamedecomp-library/scripts/refresh.py` re-fetches the catalog sources and re-harvests GitHub metadata (needs `gh auth login`); `refresh/sync_modder_kb.py --pull` then `refresh/harvest_gotchas.py` refresh the upstream snapshot; `refresh/build_knowledge.py` validates and regenerates the notes, experiments and graph data; `scripts/selftest.py` validates the suite and runs the golden-query relevance tests (also run by CI). Add notes for new catalog entries in `scripts/refresh/overlay.py`. Contribute knowledge as experiments, findings or field notes (`hub.py template ...`). When you find a ranking bug, add a golden query with a `regression` note instead of fixing it silently.

## Sources and credit
GameDecompLibrary (SolarFren), Game-Decompilations (Samidy), decompedia (decompals), universal-modder (Rehan and contributors, MIT), and the individual projects named throughout (fromsoftware-rs, Thief 3 SDK, BW1, AVP2, LEGOLAND, isle/reccmp, Halo CE decomp, objdiff, asm-differ, bsa-rs, esplugin, libloadorder, pelite, iced, binrw, unity-rs, jak-project, UnleashedRecomp...). See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Only facts and paraphrases are redistributed; each project's own repository is the authority.

## Limits
The graph, findings and experiments are small and come mostly from one project (OpenOblivion), one game and one data slice, so family-level claims are rare and most edges are `documented`; a missing edge means unknown. Retrieval is BM25 with graph-alias expansion, not semantic search. About 90 catalog entries are metadata-only; platform/type for list-sourced entries are derived and can be wrong; AI-policy flags are incomplete; progress numbers age quickly; scripts were tested on Linux with Steam game files. See `skills/gamedecomp-library/references/source-notes.md`.

## Licence
MIT for the original content in this repository (see [`LICENSE`](LICENSE)). Third-party material keeps its own licence (see notices).

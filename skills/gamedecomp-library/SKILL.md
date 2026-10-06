---
name: gamedecomp-library
description: START HERE for any game reverse-engineering, decompilation, modding, porting or asset-extraction task. Institutional memory for AI agents: ~790 game decompilation and RE tool projects (platforms, compilers, toolchains, progress, licences, AI-contribution policies), 59 upstream modding field notes plus this repo's own notes, a symptom-first `diagnose` command, structured experiment and dead-end records with a `tried` check, evidence-tagged findings, a typed research graph (games, engines, Havok/Bullet physics, techniques, projects, formats, problems), 12 engine playbooks, golden-query regression tests, and sibling skills (decomp-matching-workflow, re-binary-recon, game-hooking-patterns, bethesda-gamebryo-re, halo-engine-re, engine-reimplementation, game-asset-formats). Use before researching any game or engine ("has anyone decompiled/modded X?", "what compiler does Y use?", "player shakes on stairs", "has this been tried?"), when choosing tools, and when finishing a task so lessons and failed approaches are written back. Query with scripts/hub.py and scripts/query.py; never read whole datasets into context.
---

# Game decompilation and RE compendium (agent entry point)

This skill is a **retrieval layer**: a structured dataset plus tools so you can find the right project, field note or method in seconds and then read only that file. The knowledge itself lives in the dataset (`data/`), in six sibling skills, and in upstream sources that the dataset points to.

## Use it like this
```bash
cd <this skill>/scripts
python3 hub.py prior-art "oblivion"                       # entry point: graph card, dead ends, findings, projects, notes, gotchas, refs (read the top hit of each)
python3 hub.py diagnose "player shakes while walking upstairs"   # symptom first: likely subsystems, prior incidents, causes, oracles, failed approaches, next steps
python3 hub.py tried "lua onFrame camera smoothing"       # before trying something: was it tried, did it fail, why, what instead
python3 hub.py graph find project --has msvc --has havok --has gamebryo --rel reverse_engineered:movement   # typed relationships; graph show <term>, path A B
python3 hub.py show exp:EXP-OO-001                        # one record in full (also finding:<id>, node:<alias>, gotcha:<note>#<n>, project:<id>)
python3 hub.py search "MSVC RTTI vtable" [--source refs,notes,experiments,gotchas,findings,projects]
python3 query.py --platform "Windows" --compiler MSVC --min-progress 50     # structured filters over the catalog
python3 query.py --id thief3 --full                       # one catalog entry in full (+ local clone path); --ai ai-ok for AI-friendly projects
python3 hub.py template experiment|finding|edge|note      # write knowledge back; python3 hub.py snippet = paste-ready text for a project's AGENTS.md
```
Output names where the full text lives (a URL, a record id, a skill file). Read that, not everything. Results carry evidence levels (guessed < inferred < documented < static < verified) and scope (build / project / family): discount weak ones, and a **project**-scoped result is one project's choice, not an engine fact. `!!` marks a failed or partial experiment. A missing record or edge means *unknown*, not *no*.

## What is in the dataset
| File | Content |
|---|---|
| `data/catalog.json` / `.tsv` | 790 projects: platform, type, compilers/tools/build styles detected, progress, licence, stars, push date, `depth`, `ai` policy flag, summary/note, which skill covers it |
| `data/field-notes.json` | 59 universal-modder notes (games + techniques): engine, route, tools, anti-cheat, status, gotcha counts, summaries, URLs |
| `data/playbooks.json` | 12 engine playbooks (unity, unreal, source, bethesda, native, retro-decomp, big-frameworks...) |
| `data/modder-skills.json` | universal-modder's 10 skills (mod-any-game loop, game-recon, reverse-engineering, mashup-mods...) |
| `data/sources.json` | the data sources, licences, snapshots, refresh commands |
| `data/graph.json` | research graph generated from `knowledge/graph`: typed nodes and evidence-tagged edges, atomic findings, experiment nodes (see `references/research-graph.md`) |
| `data/experiments.json` | structured experiment / dead-end records (symptom, hypothesis, change, oracle, result, why, next, unverified) |
| `data/local-notes.json` / `modder-gotchas.json` | this repo's field notes with parsed gotchas; short extracts of the 684 upstream gotchas (symptom, cause) for `diagnose` |
Data resolves from this skill's folder, else from a download cache of the public repo (`madpai/game-decomp-compendium`), so a bare SKILL.md plus network is enough.

## Which sibling skill do I need?
| Task | Skill |
|---|---|
| Matching decomp, objdiff/dtk/splat/reccmp, naming functions, running many agents on RE work, compiler idioms | `decomp-matching-workflow` |
| Triage an exe/dll, RTTI class map, string -> function, signatures | `re-binary-recon` (scripts tested on x86 and x64) |
| Hooking/modding a running single-player game, loaders, fromsoftware-rs patterns | `game-hooking-patterns` |
| Oblivion/Gamebryo/Bethesda formats, scripts, dialogue, Havok collision and the player controller, OpenOblivion findings | `bethesda-gamebryo-re` |
| Halo tags/caches, Halo 3 MCC reading, Halo decomp map | `halo-engine-re` |
| Ports, recompilation, clean-room engines, Android, approach selection | `engine-reimplementation` |
| Unknown files, archive/mesh/animation/texture parsers, parser safety | `game-asset-formats` (has `identify.py`) |
Method and checklists for all of them: `references/agent-method.md`.

## Rules that apply to everything
1. Own copy of the game only; offline/single-player for runtime work; never bypass anti-cheat or DRM; never touch online clients with anti-cheat.
2. Never commit or publish game files, extracted assets, raw decompiler output, disassembly, tables derived from the executable, or leaked material. Describe findings in your own words; keep short snippets of your own code.
3. Respect each project's AI policy (`ai` field; `human-only` projects are not ingested by `clone.sh`) and never open issues/PRs on the user's behalf unless asked; disclose AI help where policy asks.
4. Evidence levels (static / verified / inferred / guessed) on every fact; an oracle for every claim; stop after ~3 identical failures.
5. Prefer the lightest route that reaches the goal (data -> loader API -> managed patch -> native hook -> reimplementation).

## Keeping it fresh
- `python3 scripts/refresh.py` re-fetches the library catalog and re-harvests changed repos (needs `gh auth login`); `python3 scripts/refresh/sync_modder_kb.py --pull` refreshes the universal-modder snapshot. New entries need a note in `scripts/refresh/overlay.py` (what it is, depth, AI policy).
- `scripts/clone.sh <id>` shallow-clones a catalog project for reading (`--deep` fetches all `depth=deep` entries, ~600 MB).
- `scripts/selftest.py` validates the skill suite (frontmatter, links, scripts compile, data loads, graph/experiments up to date) and runs `scripts/golden.py`, the golden-query relevance tests (`tests/golden_queries.json`). **Found a ranking bug? Add a golden query with a `regression` note; do not fix silently.**
- Write knowledge back (`references/project-integration.md`): an experiment for every failed or partial attempt, a finding for each reusable measured fact, a field note for traps; rebuild with `scripts/refresh/build_knowledge.py`. Upstream submissions only with the user's approval.

## Files
`references/agent-method.md` (operating manual + field-note template), `references/research-graph.md` (graph, findings, experiments: schema, levels, how to add), `references/project-integration.md` (feedback loop + paste-ready project snippet), `references/source-notes.md` (how the data was built, licences, known gaps), `templates/`, `tests/golden_queries.json`, `data/`, `scripts/` (hub.py, search_core.py, diagnose.py, rgraph.py, golden.py, query.py, common.py, refresh.py, clone.sh, selftest.py, refresh/*).

---
name: gamedecomp-library
description: START HERE for any game reverse-engineering, decompilation, modding, porting or asset-extraction task. A searchable compendium for AI agents of ~790 game decompilation and RE tool projects (platforms, compilers, toolchains, progress, licences, AI-contribution policies), 59 agent-written modding field notes with gotchas, 12 engine playbooks, and a suite of sibling skills (decomp-matching-workflow, re-binary-recon, game-hooking-patterns, bethesda-gamebryo-re, halo-engine-re, engine-reimplementation, game-asset-formats). Use before researching any game or engine ("has anyone decompiled/modded X?", "what compiler/toolchain does Y use?", "how do projects on platform Z work?"), when choosing tools, and when you need prior art, exemplars, or the right sibling skill. Query with scripts/hub.py (cross-source search, prior-art) and scripts/query.py (structured filters); never read the whole catalog into context.
---

# Game decompilation and RE compendium (agent entry point)

This skill is a **retrieval layer**: a structured dataset plus tools so you can find the right project, field note or method in seconds and then read only that file. The knowledge itself lives in the dataset (`data/`), in six sibling skills, and in upstream sources that the dataset points to.

## Use it like this
```bash
cd <this skill>/scripts
python3 hub.py prior-art "oblivion"                    # grouped: projects, field notes, playbook, skill sections
python3 hub.py search "anti-cheat easyanticheat" --source notes,playbooks
python3 hub.py search "inline budget tie-break" --source refs
python3 query.py --platform "Windows" --compiler MSVC --min-progress 50     # structured filters over the catalog
python3 query.py --tool objdiff --platform GameCube --sort progress
python3 query.py --id thief3 --full                    # one entry in full (+ local clone path)
python3 query.py --ai ai-ok                            # projects that use/welcome AI assistance
python3 hub.py sources                                 # what the data is made of, licences, snapshot dates
```
Output names where the full text lives (a URL, a local clone, or a skill file). Read that, not everything.

## What is in the dataset
| File | Content |
|---|---|
| `data/catalog.json` / `.tsv` | 790 projects: platform, type, compilers/tools/build styles detected, progress, licence, stars, push date, `depth`, `ai` policy flag, summary/note, which skill covers it |
| `data/field-notes.json` | 59 universal-modder notes (games + techniques): engine, route, tools, anti-cheat, status, gotcha counts, summaries, URLs |
| `data/playbooks.json` | 12 engine playbooks (unity, unreal, source, bethesda, native, retro-decomp, big-frameworks...) |
| `data/modder-skills.json` | universal-modder's 10 skills (mod-any-game loop, game-recon, reverse-engineering, mashup-mods...) |
| `data/sources.json` | the data sources, licences, snapshots, refresh commands |
Data resolves from this skill's folder, else from a download cache of the public repo (`madpai/game-decomp-compendium`), so a bare SKILL.md plus network is enough.

## Which sibling skill do I need?
| Task | Skill |
|---|---|
| Matching decomp, objdiff/dtk/splat/reccmp, naming functions, running many agents on RE work, compiler idioms | `decomp-matching-workflow` |
| Triage an exe/dll, RTTI class map, string -> function, signatures | `re-binary-recon` (scripts tested on x86 and x64) |
| Hooking/modding a running single-player game, loaders, fromsoftware-rs patterns | `game-hooking-patterns` |
| Oblivion/Gamebryo/Bethesda formats, scripts, dialogue, OpenOblivion findings | `bethesda-gamebryo-re` |
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
- `scripts/selftest.py` validates the skill suite (frontmatter, links, scripts compile, data loads).
- Contribute new knowledge as a field note (template in `references/agent-method.md`) in the user's repo; upstream submissions only with the user's approval.

## Files
`references/agent-method.md` (operating manual + field-note template), `references/source-notes.md` (how the data was built, licences, known gaps), `data/`, `scripts/` (hub.py, query.py, common.py, refresh.py, clone.sh, selftest.py, refresh/*).

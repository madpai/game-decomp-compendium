# Agent guide

This repository is a retrieval layer and method library for game reverse engineering, decompilation, modding, porting and asset extraction.

## Start here
1. Read `skills/gamedecomp-library/SKILL.md` (short).
2. Search before researching: `python3 skills/gamedecomp-library/scripts/hub.py prior-art "<game or engine>"`, then read only the files the top hits point to. Symptom first: `hub.py diagnose "<symptom>"`. Before trying an approach: `hub.py tried "<idea>"` (a `!!` result means it failed before; read why). Relationships: `hub.py graph find|show|path`.
3. Pick the sibling skill that matches the task (table in the SKILL.md) and follow its workflow. Skills point to `references/` files for depth and `scripts/` for tested tools.
4. Install the skills for repeated use: `./install.sh` (copies `skills/*` to `~/.claude/skills`), or just keep working inside this clone.

## Rules (full text in the skills)
- Owned copy of the game only; offline/single-player for runtime work; never bypass anti-cheat or DRM; never touch online clients protected by anti-cheat.
- Never commit game files, extracted assets, raw decompiler output, disassembly, tables derived from executables, keys or secrets.
- Respect AI-contribution policies (`ai` field in the catalog); never open issues or pull requests on a third party's behalf unless the user asks; disclose AI help where policy requires.
- Mark facts static / verified / inferred / documented / guessed (definitions: `skills/gamedecomp-library/references/research-graph.md`); build an oracle before scaling; stop after ~3 identical failures. Never turn one project's implementation choice into an engine fact: give it `scope: project`.
- Do not load the whole catalog into context. Use the query tools.

## Working on this repository
- This repository is the source of truth: edit under `skills/` (never in `~/.claude/skills`), then run `./install.sh` to refresh your local copy.
- Edit skills under `skills/`; keep each `SKILL.md` under 500 lines with a "pushy" description (what it does and when to use it); put depth in `references/`.
- Data is generated: change `skills/gamedecomp-library/scripts/refresh/overlay.py` (hand notes, depth, AI policy) and re-run `refresh.py`; never edit `catalog.json` by hand.
- Run `python3 skills/gamedecomp-library/scripts/selftest.py` before committing (it validates `knowledge/`, that generated data is up to date, and the golden queries).
- Field notes live in `knowledge/` (see its README). Experiments and dead ends: `knowledge/experiments/` (rules in its README). Research graph and findings: `knowledge/graph/*.jsonl` (schema: `references/research-graph.md`). After editing any of them run `python3 skills/gamedecomp-library/scripts/refresh/build_knowledge.py` (validates schemas, evidence levels and every source pointer; regenerates `data/graph.json`, `data/experiments.json`, `data/local-notes.json` and the INDEX files). Never edit generated files by hand.
- **Write back what you learn**: a failed or partial attempt -> an experiment record; a reusable measured fact -> a finding; a trap -> a field note gotcha (`hub.py template experiment|finding|edge|note`). Workflow and quality bar: `skills/gamedecomp-library/references/project-integration.md`.
- **Retrieval quality is tested**: `scripts/golden.py` runs `tests/golden_queries.json` (also inside `selftest.py`). If you find a ranking bug, add a golden query with a `regression` note (`golden.py --stub <cmd> "<query>"` prints a stub); do not fix it silently. Keep windows wide; do not make tests brittle.
- Text style: plain, specific, evidence-tagged; paraphrase sources and name them; no bulk copying of third-party text; short snippets only, with attribution.
- Add new knowledge as an experiment, finding, field note (templates: `skills/gamedecomp-library/templates/`) or as a section in the relevant skill reference. Do not grow the catalog for its own sake: add projects only for engine/platform coverage, methodology, a known problem area, or prior art with real depth.
- Keep retrieval token-efficient: query first, return pointers, keep `SKILL.md` concise and depth in references; summarise large data instead of loading it.

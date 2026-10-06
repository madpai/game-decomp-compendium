# Agent guide

This repository is a retrieval layer and method library for game reverse engineering, decompilation, modding, porting and asset extraction.

## Start here
1. Read `skills/gamedecomp-library/SKILL.md` (short).
2. Search before researching: `python3 skills/gamedecomp-library/scripts/hub.py prior-art "<game or engine>"`, then read only the files the top hits point to.
3. Pick the sibling skill that matches the task (table in the SKILL.md) and follow its workflow. Skills point to `references/` files for depth and `scripts/` for tested tools.
4. Install the skills for repeated use: `./install.sh` (copies `skills/*` to `~/.claude/skills`), or just keep working inside this clone.

## Rules (full text in the skills)
- Owned copy of the game only; offline/single-player for runtime work; never bypass anti-cheat or DRM; never touch online clients protected by anti-cheat.
- Never commit game files, extracted assets, raw decompiler output, disassembly, tables derived from executables, keys or secrets.
- Respect AI-contribution policies (`ai` field in the catalog); never open issues or pull requests on a third party's behalf unless the user asks; disclose AI help where policy requires.
- Mark facts static / verified / inferred / guessed; build an oracle before scaling; stop after ~3 identical failures.
- Do not load the whole catalog into context. Use the query tools.

## Working on this repository
- Edit skills under `skills/`; keep each `SKILL.md` under 500 lines with a "pushy" description (what it does and when to use it); put depth in `references/`.
- Data is generated: change `skills/gamedecomp-library/scripts/refresh/overlay.py` (hand notes, depth, AI policy) and re-run `refresh.py`; never edit `catalog.json` by hand.
- Run `python3 skills/gamedecomp-library/scripts/selftest.py` before committing.
- Text style: plain, specific, evidence-tagged; paraphrase sources and name them; no bulk copying of third-party text; short snippets only, with attribution.
- Add new knowledge as a field note (template: `skills/gamedecomp-library/references/agent-method.md`) or as a section in the relevant skill reference.

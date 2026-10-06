# Using the compendium from a project, and writing back (the feedback loop)

The compendium is institutional memory for reverse-engineering and porting work. It is a **research dependency**, not an engine dependency: a project never imports it, builds against it or breaks without it. It only changes how research is done and where lessons end up.

```
Compendium  ->  active project  ->  new discovery / failed experiment / technique
     ^                                             |
     |                                             v
 future projects  <-  Compendium  <-  field note, finding, experiment record
```

## Paste this into a project's AGENTS.md / CLAUDE.md
(Also printed by `hub.py snippet`. Applies to OpenOblivion, MegaMod Showdown, Open Asset Lab and any future decomp or reimplementation project.)

<!-- snippet:start -->
## Research dependency: game-decomp-compendium (optional; not a runtime dependency)
Before starting engine, file-format or reverse-engineering research, check what is already known. Repo: https://github.com/madpai/game-decomp-compendium (clone it, or run its `./install.sh`). If it is unreachable, say so and continue.
1. **Query first.** `python3 <compendium>/skills/gamedecomp-library/scripts/hub.py prior-art "<game or engine>"`. For a symptom: `hub.py diagnose "<symptom>"`. Before trying an approach: `hub.py tried "<idea>"` (it warns when the idea was already tried and why it failed).
2. **Read little.** Open the applicable skill and only the top hits (`hub.py show <id>`). Never load the whole catalog or whole skill folders into context.
3. **Web research only for gaps** or for anything newer than the compendium's snapshot; say what the compendium lacked.
4. **Evidence discipline.** Mark each important claim static / verified / inferred / documented / guessed, with the oracle that backs it and what remains unverified. One project's implementation choice is not an engine fact. Owned copies only, offline/single-player for runtime work, no DRM or anti-cheat bypass, no game files, decompiler dumps, executable-derived tables or addresses in repositories.
5. **Write back at completion.** Reusable findings, techniques and every failed or partial attempt go back to the compendium: `hub.py template experiment|finding|edge|note`, then `refresh/build_knowledge.py` and `selftest.py` in the compendium. Hand the files to the owner if you cannot push; do not open issues or PRs on third-party projects unasked.
<!-- snippet:end -->

## When to write back (checklist for the end of a task or milestone)
- Did something fail, regress or turn out to be a dead end? -> one **experiment** (`failed`/`partial`), with the symptom, the change, the oracle, the numbers, why it failed (with its evidence level) and what to try instead. This is usually the most valuable record.
- Did something work? -> one **experiment** (`worked`) that says what it did *not* establish, if the method is reusable; otherwise just a finding.
- Did you measure a fact other projects could rely on? -> a **finding** (atomic claim, level, scope, build, oracle, what is unverified) and, if needed, an **edge** (`hub.py template finding|edge`).
- Did you learn how a tool, build or device behaves (a trap that cost an hour)? -> a **field note** (`hub.py template note`) with numbered symptom -> cause -> fix gotchas.
- Did you find a ranking or retrieval failure in the compendium itself? -> add a **golden query** (`golden.py --stub ...`) with a `regression` note.
Skip: anything the repository already records (code layout, git history), anything only meaningful inside one conversation, and anything that would need game data, dumps or addresses to be understood.

## Quality bar for what you write
- Exact game/build/version, the source or project, what was measured, the oracle, what remains unverified. A result and its explanation get **separate** evidence levels.
- Prefer independent confirmation (a second measurement, another project, upstream documentation) and record it (`confirmed_by`). Without it a claim stays `scope: build` or `scope: project`.
- Numbers go with their metric's name and the run or series they came from; compare rows from one binary, not single digits.
- Paraphrase third-party text, name the source, keep snippets short, respect each project's licence and AI-contribution policy (`query.py --id <project> --full` shows the `ai` flag; human-only projects are never contributed to).

## Keeping the coupling loose
- A project may keep a short "Research notes" section that links to compendium record ids (`EXP-OO-001`, `finding:...`) instead of copying them; the ids are stable.
- The project's own docs stay the place for its decisions and status tables; the compendium holds what is reusable *outside* that project.
- If the compendium is stale or missing, do the research anyway and write the records afterwards.

## Compendium side of the loop
After adding or editing records: `python3 skills/gamedecomp-library/scripts/refresh/build_knowledge.py` (validates schemas and every pointer, regenerates `data/*.json`), `python3 skills/gamedecomp-library/scripts/selftest.py` (structure + golden queries), commit sources and generated files together, push (CI repeats the selftest), then `./install.sh` to refresh `~/.claude/skills`.

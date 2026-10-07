# Update 2026-10-06 (session after the knowledge-quality phase): the loop closed once

**End of night addendum:** the airborne port was then confirmed on the owner's phone (three running jumps: rise 66.8/66.4/67.7 units, horizontal 320 to 355 units/s, owner verdict "feels more right"), after a bug in the port's own bookkeeping at 120 fps was found by a one-line on-device log (EXP-OO-017; gotcha added to the physics reference and the technique note). State: 903 selftest checks, 48 golden queries; new record text can displace older records in golden windows, so keep new records free of unrelated vocabulary and note any regression on the test. Owner rule recorded in OpenOblivion's AGENTS.md: the engine must always feel like the original, liberties only for touch/mobile play.

OpenOblivion's next movement milestone wrote back: the original's airborne laws (gravity, jump formula, per-frame
semi-implicit integration, air control) and run speed were verified on the running game and ported; records are
EXP-OO-015 (worked) and EXP-OO-016 (a failed inference from one apex), seven new findings (`oblivion-world-gravity-73-575`,
`oblivion-controller-semi-implicit-per-frame`, `oblivion-jump-height-formula`, `oblivion-air-control-relaxation`,
`oblivion-run-speed-355-6`, `oblivion-controller-state-codes`, `oblivion-grounded-state-falls-under-gravity`), the technique note
`techniques/replaying-a-character-controller-from-its-own-timesteps.md` (graph node `technique:replay-oracle`, problem
`problem:jump-height-mismatch`), four golden queries (47 pass), and updates to `character-controller-and-stairs.md`,
`physics-backend-translation.md` and the case study. A ranking regression caused by the new record (it displaced the emulator
crash record) was fixed by removing incidental vocabulary and noted on the golden test. Next measurement worth doing and
recording: the controller's **support check** (where ground becomes air; sample drops of 10 to 120 units), then step
height and slope limit. The snippet is still not pasted into OpenOblivion's AGENTS.md by the compendium; OpenOblivion's
AGENTS.md now links the compendium and the method directly.

# Handoff (written 2026-10-06, end of the "knowledge quality" phase)

## State
The compendium moved from a searchable collection to an agent-oriented research system. Foundation unchanged (790-project catalog, 8 skills, field notes, tested recon scripts); added on top: a typed research graph, structured experiment and dead-end records, evidence-tagged findings, symptom-first retrieval, golden relevance tests, a project feedback loop, and a Havok/Gamebryo physics research area. `python3 skills/gamedecomp-library/scripts/selftest.py` passes (794 checks including 43 golden queries). Skills in `~/.claude/skills` are refreshed with `./install.sh` after every change.

## Start here next session
1. `python3 skills/gamedecomp-library/scripts/hub.py prior-art "<topic>"`; symptoms: `hub.py diagnose "<symptom>"`; before an idea: `hub.py tried "<idea>"`; relationships: `hub.py graph show|find|path|stats|predicates`.
2. Read `AGENTS.md`, then `skills/gamedecomp-library/references/research-graph.md` (schema, levels, how to add records) and `project-integration.md` (feedback loop, paste-ready project snippet = `hub.py snippet`).
3. After any edit to `knowledge/`: `python3 skills/gamedecomp-library/scripts/refresh/build_knowledge.py`, then `selftest.py`, commit sources and generated files together, push, `./install.sh`.

## What is where
- `knowledge/graph/{nodes,edges,findings}.jsonl` (hand-written, validated), `knowledge/experiments/*.md` (15 records: `EXP-OO-001..014` OpenOblivion, `EXP-BW1-001`), `knowledge/games/oblivion/openoblivion-movement-collision-case-study.md`.
- Generated (never edit by hand): `data/graph.json`, `experiments.json`, `local-notes.json` (+parsed gotchas), `knowledge/INDEX.md`, `knowledge/experiments/INDEX.md`. `data/modder-gotchas.json` comes from `refresh/harvest_gotchas.py` after `sync_modder_kb.py --pull`.
- Code: `scripts/search_core.py` (BM25 + graph-alias expansion + per-kind diversification + project graph boost), `diagnose.py`, `rgraph.py` (schema, validation, queries), `golden.py` + `tests/golden_queries.json`, `refresh/build_knowledge.py` (+ `index_local_notes.py`, `index_experiments.py`).
- Physics area: `skills/bethesda-gamebryo-re/references/{havok-gamebryo-collision,character-controller-and-stairs,physics-backend-translation}.md`. A dedicated `game-physics-re` skill is not warranted yet (all evidence is Oblivion, one project); split it out when a second game or project contributes measurements.

## Decisions worth keeping
- A fifth evidence level, `documented` (an upstream statement we read but did not check), sits between `inferred` and `static`; the OpenOblivion rule table already used it.
- Results and mechanisms have separate levels in experiments (`level`, `why_level`); a Lua-filter regression is `verified` / `inferred`.
- `scope` (build / project / family) keeps one project's choice from becoming an engine fact; `family` needs `confirmed_by`.
- Missing edge = unknown. Orphan nodes fail the build (no speculative graph).
- Ranking bugs get a golden query with a `regression` note. Two were found and fixed this phase: N64 queries returning non-N64 projects, and findings flooding a one-word query.
- Phone testing for OpenOblivion stays paused (owner, 2026-10-06); nothing here depends on it, but several experiment records list phone retests as pending.

## Known limitations
- Nearly all movement/collision evidence is one game, one project and one data slice (Vilverin); most graph edges are `documented`, only a few are `verified`/`static`.
- Unmeasured and listed as open questions: the original controller's step height, slope limit, jump and run speed; the Havok layer filter matrix; terrain height-field collision; packed-strip prevalence outside Oblivion; whether MOPP-culled queries equal full-mesh queries.
- The archive-parsing boundary checklist is general knowledge, not a recorded incident; the first real incident should become an experiment.
- Retrieval is BM25 with aliases and cues, not semantic search; a symptom with no cue word and no word overlap returns nothing (by design, it says so).
- The project snippet is not yet pasted into OpenOblivion, MegaMod Showdown or Open Asset Lab; do that only when the owner asks (it edits other repositories).
- `modder-gotchas.json` is a snapshot (revision in its meta); refresh it after `sync_modder_kb.py --pull`.

## Next three highest-value improvements
1. **Close the loop in one live project**: paste the snippet into OpenOblivion's AGENTS.md, then make the next movement milestone write its experiments back (e.g. measure the original's step height/slope and run speed with the sampler on the owner's copy, then record findings with `confirmed_by` if a second source appears).
2. **Second-source evidence for the physics area**: census a few Fallout 3 / Skyrim NIFs (block types, packed strips, scales) to turn `guessed` edges into `static` ones and decide whether `game-physics-re` should become its own skill; add an independent check of the x7 scale on another shape class.
3. **Grow dead ends from other projects, not the catalog**: read the AGENTS.md/notes of the deep-read decomp projects (Thief 3, LEGOLAND, AVP2, isle, jak) for recorded failures and add `EXP-*` records with `documented` levels; add a handful of golden queries per new area. Keep the catalog changes to coverage gaps.

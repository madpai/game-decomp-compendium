# Research graph, findings and experiments: schema and rules

The compendium keeps three small, auditable record types beside the project catalog and the field notes. All are plain text, diff-friendly and validated by `scripts/refresh/build_knowledge.py`; nothing is a database.

| Record | Source of truth | Generated | Query with |
|---|---|---|---|
| Nodes and edges (games, engines, technology, techniques, projects, formats, problems, subsystems) | `knowledge/graph/nodes.jsonl`, `edges.jsonl` | `data/graph.json` | `hub.py graph show/find/path/stats/predicates` |
| Findings: atomic claims with provenance | `knowledge/graph/findings.jsonl` | graph nodes `finding:*` | `hub.py show finding:<id>`, `diagnose`, `prior-art` |
| Experiments and dead ends | `knowledge/experiments/*.md` | `data/experiments.json`, graph nodes `exp:*` | `hub.py tried`, `experiments`, `show exp:<ID>` |

## Evidence levels (every edge, finding and experiment carries one)
`guessed` < `inferred` < `documented` < `static` < `verified`; the order exists for filtering (`--min-level`), not as a probability.
- **static**: read directly from a binary, source tree or data file; no running, no independent oracle.
- **verified**: measured or observed with an oracle. Independent confirmation is recorded separately (`confirmed_by`).
- **inferred**: our reasoning from evidence we hold; the step from evidence to claim is not measured.
- **documented**: stated by an upstream source (spec, wiki, README, project docs) that we read but did not check.
- **guessed**: plausible and unchecked; an edge or finding at this level must say how to check it.
Experiments carry two levels: `level` for the result and `why_level` for the mechanism (a measured regression with an unproven cause is `verified` / `inferred`).

## Scope (never turn one project's choice into an engine fact)
`build`: a fact about named build(s), slice or data. `project`: one project's implementation choice or an upstream pin. `family`: holds across builds or games and **requires `confirmed_by`**. Project-scoped predicates (`donor_engine`, `approach`, `problem`, `reverse_engineered`, `uses_*`) describe the project and are never lifted onto the game or engine; edge types enforce this (`hub.py graph predicates` shows what each predicate may connect).

## Adding knowledge
1. **Node** (only if an edge, finding or experiment will use it; orphans fail the build): one JSON line in `nodes.jsonl` with `id` (`type:slug`), `name`, `aliases` (unique across nodes), `summary`, and for subsystems/problems `cues` (symptom words that make `diagnose` suggest it).
2. **Edge**: `[subject, predicate, object, level, source, note]` in `edges.jsonl` (`hub.py template edge`). `source` is one or more `;`-separated pointers: `ref:<skill>/<file>[#heading]`, `note:<path>`, `exp:<ID>`, `finding:<id>`, `catalog:<id>`, `playbook:<id>`, `repo:<owner>/<name>/<path>`, `url:https://...`. Every pointer must resolve. Say in `note` exactly which part is established.
3. **Finding** (`hub.py template finding`): `claim` (atomic, 420 chars at most), `level`, `scope`, `build` (required for scope build), `about`, `oracle` (required for static/verified), `source`, `unverified` (always required), `confirmed_by`.
4. **Experiment** (`hub.py template experiment`, rules in `knowledge/experiments/README.md`).
5. `python3 skills/gamedecomp-library/scripts/refresh/build_knowledge.py` then `python3 skills/gamedecomp-library/scripts/selftest.py`; commit sources and generated files together (CI fails on stale generated data).
Never record game files, decompiler output, executable-derived tables, hex addresses or private paths; the build rejects the obvious ones.

## Questions the graph answers
- `hub.py graph find project --has msvc --has havok --has gamebryo --rel reverse_engineered:movement` -> projects whose target game reaches all three terms and that recovered movement (each hop printed with its weakest evidence level).
- `hub.py graph find technique --rel applies_to:oblivion`; `graph find project --has n64 --rel "approach:static recompilation"`; `graph find project --rel failed:camera` (projects with a failed or partial experiment about the camera).
- `hub.py graph show subsystem:player-controller` (edges, experiments, findings); `hub.py graph path openoblivion havok` (why two things are related).
A missing edge means **unknown**, not no. Terms resolve through node ids, names and aliases; `--has` follows property edges up to three hops.

## Growth rules
Add a record when it saves a future agent from rediscovering something, not to raise a count: a dead end, a measured fact with its oracle, a relationship a query needs. Prefer fewer, well-sourced edges. Catalog growth follows the same rule (coverage of an engine or platform, methodology, a known problem area, prior art with real depth).

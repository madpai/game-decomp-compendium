# Experiments and dead ends

Structured records of things that were tried: what was believed, what was changed, how it was judged, what happened and why. **Failed and partial results are first-class** - a recorded dead end saves the next agent the same afternoon. Successes are recorded separately and with the same fields, so a "worked" result states what it did *not* establish.

Retrieve with `hub.py tried "<idea>"` (warns when a similar approach already failed), `hub.py experiments [--result failed] [--project X]`, `hub.py show exp:EXP-OO-001`; `hub.py diagnose "<symptom>"` and `prior-art` surface them too.

## Rules
- One file per experiment: `exp-<project>-<nnn>-<slug>.md`, id `EXP-<PROJECT CODE>-<NNN>`, template `skills/gamedecomp-library/templates/experiment.md` (or `hub.py template experiment`).
- Two evidence levels: `level` for the result, `why_level` for the mechanism. A measured regression with an unproven cause is `level: verified`, `why_level: inferred`. Say what would isolate it under **Next** or **Unverified**.
- `scope: build` for a fact about named data/build; `scope: project` for one project's choice or an upstream pin. An experiment never has family scope: a claim that holds across games is a *finding* with `confirmed_by` in `knowledge/graph/findings.jsonl`.
- `failed`/`partial` need a real **Why** and **Next**. Do not record a failure you cannot describe; record `inconclusive` and what blocked the conclusion.
- Numbers belong in **Result** with the metric's name and which runs they come from; compare rows, not single digits.
- Never include game files, decompiler output, executable-derived tables, hex addresses, keys or private paths (the build rejects them). Private evidence is referred to by name only.
- Link experiments into the graph through `about:` (node ids must exist in `knowledge/graph/nodes.jsonl`; add the node if the experiment needs one).
- After editing run `python3 skills/gamedecomp-library/scripts/refresh/build_knowledge.py`, then `python3 skills/gamedecomp-library/scripts/selftest.py`.

The generated table is [INDEX.md](INDEX.md).

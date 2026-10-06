# Agent operating manual for game reverse-engineering work

A compact method that combines the best practices seen in the corpus (Thief 3/BW1/AVP2 agent workflows, universal-modder's loop, OpenOblivion's practice). Use it as a checklist at the start of any game RE, decomp, modding or porting task.

## 0. Before anything
1. **State the goal in one sentence and pick the cheapest route that reaches it** (`decomp-matching-workflow` section 0, `game-hooking-patterns` route table, `engine-reimplementation` approach table).
2. **Search prior art**: `python3 scripts/hub.py prior-art "<game or engine>"` (symptom first: `hub.py diagnose "<symptom>"`; before an approach: `hub.py tried "<idea>"`). Read the top hit of each group. Then check the web for anything newer than the snapshot (dates are in `data/sources.json`).
3. **Check legality and policy**: owned copy only; offline/single-player only for runtime work; no anti-cheat/DRM bypass; project AI policies (`query.py --id X --full`).
4. **Start a journal** (`MODLOG.md`/handoff doc): paths, ids, versions, formats, class names, what failed and why, next step. Anything not in the journal is lost at the next context compaction.

## 1. Recon
`re-binary-recon` (pe_info -> rtti_scan -> string_xrefs -> aob_scan), `game-asset-formats` (identify), `bethesda-gamebryo-re`/`halo-engine-re` for family facts. Record build ids (PE timestamp, file hashes).

## 2. Source of truth
Read real code/data, never guess. Measure data over the whole file. Mark each fact **static / verified / inferred / documented / guessed** (definitions in `references/research-graph.md`); upgrade only with an independent second source. Give a result and its explanation separate levels, and never turn one project's choice into an engine fact.

## 3. Vertical slice
One thing end to end with placeholders; commit it; widen afterwards.

## 4. Oracles (pick before coding)
Round trip; trace replay; real-data assertions over all records; scripted scene + screenshot you actually look at; game log; byte-matching build; headless bench; publish check. Prove the oracle is live. Circuit breaker: ~3 identical failures -> stop, write down what you know, change approach or ask.

## 5. Scale out only with a gate
Parallel agents need: claim queue (`decomp-matching-workflow/scripts/claimq.py`), scratch-only workers, a gate that decides acceptance, one-line JSON reports, a lead who integrates and reviews (`references/agent-swarm-playbook.md`).

## 6. Record and share
Update the project's docs with measured facts and the rule-status table. Write an **experiment record** for every failed or partial attempt (`hub.py template experiment`), a **finding** for each reusable measured fact, and a **field note** (template below) for anything the next agent would lose an hour to. Workflow and checklist: `references/project-integration.md`. Share upstream (universal-modder PR, project docs) only with the user's approval, never with game files, decompiled dumps, secrets or exe-derived tables.

## Field-note template (compatible with universal-modder's `knowledge/TEMPLATE.md`)
```markdown
---
kind: game            # or technique
title: "<what you built or learned>"
game: "<game>"
games_also: []
game_version: "<exact build that worked>"
platform: windows
engine: <engine key or unknown>
route: <data|asset-only|loader-api|managed-patch|native-hook|reimplementation|decomp-recomp|passthrough|emulator|other>
tools: []
anti_cheat: "<what protects it and how you stayed clear>"
status: <idea|in-progress|working|released|abandoned>
agents: ["<agent (model)>"]
date: YYYY-MM-DD
tags: []
---
# Title
> 2-4 sentences: what, where, route, whether verified and how.
## Setup            exact versions
## Route and why
## How the game works     in your own words; no pasted decompiled code or game data
## Build steps
## Verification     the oracle, and what you did NOT verify
## Gotchas          numbered: symptom -> cause -> fix
## Open questions
```
Rules: honest status; name the agent/model; list what you did not verify; snippets of your own code only (short); no secrets.

## Token discipline
Never load the whole catalog into context: use `query.py`/`hub.py` and read only the files a hit points to. SKILL.md files are small and point to references; read references on demand. Keep outputs of big tools in files and summarise.

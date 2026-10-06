---
id: EXP-XX-001                 # EXP-<PROJECT CODE>-<NNN>; the file is named <id lowercase>-<slug>.md
title: "<what was tried, in one line>"
project: <project slug>        # a node in knowledge/graph/nodes.jsonl as project:<slug>
result: failed                 # worked | failed | partial | inconclusive
level: verified                # evidence for the RESULT: static | verified | inferred | documented | guessed
why_level: inferred            # evidence for the WHY (often weaker than the result: say so)
scope: project                 # build = a fact about named build(s)/data | project = one project's choice or an upstream pin
status: final                  # final | open | superseded
date: YYYY-MM-DD               # when the experiment ran
agents: ["<agent (model)>"]
about: [subsystem:camera]      # graph node ids this is about (subsystem:, tech:, engine:, struct:, technique:, problem:, game:)
games: [game:oblivion]
tags: []
related: []                    # other experiment ids (e.g. the one that followed)
---

# <title>

## Symptom
What was observed, from whom, on which build. Quote the log line or metric, not just the feeling.

## Hypothesis
What you believed would fix or explain it, and why that seemed likely.

## Environment
Exact versions, pins, data, hardware, driver or probe, metric name. Enough for someone else to repeat it.

## Change
The one thing that was changed (or the sequence of changes if iterated). No pasted game code or dumps.

## Oracle
How the result was judged: the measurement, the control run, the pass gate, what a failure would have looked like.

## Result
What happened, with the numbers. If worked/failed differ by case (synthetic vs real data), say so per case.

## Why
Why it worked or failed. Mark the evidence level of the mechanism. If the cause is a good explanation but was not isolated, say that plainly.

## Next
The recommended next direction. For failed or partial results this is what to try instead (and what not to repeat).

## Unverified
What was NOT checked: other builds, other data, real devices, confounds, one-session measurements.

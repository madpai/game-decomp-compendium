---
id: EXP-OO-001
title: "Lua onFrame grounded-eye filter against the per-tread camera jolt on stairs"
project: openoblivion
result: failed
level: verified
why_level: inferred
scope: project
status: final
date: 2026-10-01
agents: ["Claude Code (Sonnet 5.5), recorded from project docs and private metrics"]
about: [subsystem:camera, subsystem:player-controller, engine:openmw, problem:stair-camera-jolt, technique:paired-same-binary-probe]
games: [game:oblivion]
tags: [stairs, camera, smoothing, lua, onFrame, eye-height, regression]
related: [EXP-OO-002]
---

# Lua onFrame grounded-eye filter against the per-tread camera jolt on stairs

## Symptom
Owner feedback on the phone build 0.3: walking, stopping, collision, jumping and look work, and stair ascent and descent work, but each tread produces an uncomfortable vertical view jolt (the camera bounces or shakes) in both directions. An earlier answer about "catching and slowing" was superseded by this clarification, so the physical traversal was not the defect.

## Hypothesis
The jolt is the camera following the player root through discrete tread rises. A bounded, exponentially smoothed vertical eye offset (100 ms response, lag capped at 48 units, reset on jump, airborne, swimming, cell change, large position change, pause and long frame gaps), applied only while grounded and only for the missing-head fallback camera, would remove the jolt without touching player motion. Implemented in Lua in the `onFrame` hook.

## Environment
OpenOblivion desktop probe, OpenMW 0.52 pin, software GL, same binary and the same scripted controls driver for raw and filtered runs. Two routes: the generated stair fixture (twenty 16-unit rises, 24-unit treads) and the real Vilverin entrance stairs. Metric: view (camera) vertical-velocity variation, lower is smoother, plus the walking-response, stopping and jump/landing gates. Run on 2026-10-01; numbers come from private evidence runs named `original-stair-*-04b` and `player-entrance-stairs-*-04`.

## Change
An opt-in Lua filter adding a bounded vertical focal offset in `onFrame`. Player position, movement commands, look and the native camera collision tests were not modified. Excluded from the phone packager.

## Oracle
Paired raw and filtered runs of one binary and one driver, with the movement gates still required to pass. The comparison metric is view vertical-velocity variation. Raw baselines differ between runs (the real ascent baseline was 1206.7 here and 1321.4 in the later native comparison), so compare rows and not single digits.

## Result
Mixed, and the real-stairs result decided it. Improved: generated fixture ascent 2214.5 to 484.6 and descent 2092.4 to 449.6 (about -78%), real Vilverin descent 2414.0 to 704.3 (-71%). Regressed: real Vilverin ascent 1206.7 to 3008.3 (+149%, worse than no filter). The filter was withheld from phone QA; the private experimental 0.4 APK was not deployed, and the owner's later liking of the 0.5 stairs must not be attributed to this experiment.

## Why
Inferred, not isolated. The engine invokes Lua `onFrame` before physics and before the camera update (read from the donor engine), so a height correction computed there can arrive out of phase with the solved step; that fits the increased ascent variation. It does not explain why real descent improved while real ascent regressed. No run changed only the timing: the native version in EXP-OO-002 differs in language and placement, so the phase explanation is the best fit, not an established cause.

## Next
Apply the correction after physics inside the native camera position update and compare with the same paired probe (EXP-OO-002). To isolate timing from implementation, also try the Lua filter from a post-physics hook if the donor exposes one, or the C++ filter pre-physics. Do not re-run this variant on phones: a synthetic stair fixture passing is not evidence for the real stairs.

## Unverified
That phase is the cause; why descent improved; any phone perception of this variant (it never shipped); other frame rates; other staircases than the fixture and Vilverin's entrance.

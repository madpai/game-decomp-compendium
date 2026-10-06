---
id: EXP-OO-012
title: "Animate TES4 NPCs: KF transform decoding, then a T-pose caused by parts binding to a private skeleton copy"
project: openoblivion
result: worked
level: verified
why_level: inferred
scope: build
status: final
date: 2026-10-03
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [subsystem:animation, problem:skeleton-bone-name-mismatch, fmt:nif, engine:openmw, game:oblivion]
games: [game:oblivion]
tags: [animation, kf, skeleton, t-pose, skinning, attachment, bone-names]
related: []
---

# Animate TES4 NPCs: KF transform decoding, then a T-pose from parts binding to a private skeleton copy

## Symptom
Two stages. First, the unchanged native renderer loaded zero tracks from the owner's third-person idle and forward-walk KF roots (NIF 20.0.0.4). Second, after decoding worked and the animation clock ran, the first live probe still showed a T-pose. Earlier, the donor's part attachment had also failed on a missing Groin node because Oblivion's skeleton uses other bone names.

## Hypothesis
Stage one: the renderer's KF loader does not understand the 20.0.0.4 `NiControllerSequence` layout (string-palette bone names, compressed cubic-spline channels, WXYZ rotation). Stage two: skinned parts resolve a different skeleton instance than the one being animated.

## Environment
Native Linux and Android ARM64 builds of the OpenMW pins with the animation receipt; Vilverin probes with five NPCs; independent PyFFI parsing and a separately written float64 de Boor evaluator as cross-check; the owner's idle and walk clips.

## Change
A KF adapter decoding transform tracks with bounded evaluators; then an original TES4 attachment selector that copies the renderable's local subtree, replacing an empty filter that copied each part's private skeleton so skinned parts resolve the actor's animated bones. Skeleton targets missing from the human skeleton (nine tail targets) are reported and skipped, not mapped to invented bones.

## Oracle
Decoder: 73 transform tracks loaded from each clip (idle: 23 compressed spline, 50 ordinary, two float tracks outside the adapter); 1,525 compressed channel samples cross-checked with maximum component error 7.3e-7 against a tolerance of 2e-5; 8,906 finite sampled poses. Live: five NPCs with at least 13 clock samples per actor and two natural loop wraps, plus inspected private captures showing lowered arms and the original idle pose.

## Result
Worked on desktop probes (decoder and live idle). Phone rendering of idle was pending. Locomotion and attack selection, first-person hands, facial and morph tracks, equipment masking and special idles remain open.

## Why
Inferred for stage two (the private-skeleton copy was found by inspection and fixed by the subtree copy; the capture changed accordingly). Stage one is verified by the cross-check. The skeleton has no Groin, Chest, Neck, Head or Right Hand nodes, so any code that looks bones up by another game's names fails: bone naming is a data fact of each game's skeleton, not an engine constant.

## Next
Locomotion selection from movement state, first-person hands, facial tracks, equipment masking, then phone acceptance of idle. When a skeleton "loads" but animation or attachments are wrong, list the skeleton's node names and compare them with what the donor looks up, then check which skeleton instance each skinned part binds to.

## Unverified
Original-executable playback; any locomotion comparison; the two float tracks; phone rendering.

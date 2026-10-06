---
id: EXP-OO-008
title: "Port the original's settings-based ground-speed formula into the donor's maximum-speed function"
project: openoblivion
result: worked
level: verified
why_level: inferred
scope: build
status: final
date: 2026-10-03
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [subsystem:player-controller, game:oblivion, engine:openmw, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [gait, speed, formula, settings, static-analysis]
related: [EXP-OO-007]
---

# Port the original's settings-based ground-speed formula into the donor's maximum-speed function

## Symptom
No second gait after three binding experiments (EXP-OO-007).

## Hypothesis
The original computes ground speed from game settings and the player's Speed and Athletics, not from animation state. Reproducing that formula in the donor's maximum-speed function gives the original's speeds regardless of animation.

## Environment
The executable's character speed routine and the settings it registers at start-up, read statically from the Steam build; the owner's master supplies the overriding values (walk 90 to 130, run multiplier 3, no-weapon 1.1, sneak 0.6) and the Player record (Speed 40, Athletics 5); desktop probe with the same binary. One setting (the run athletics multiplier) is absent from the master and takes the executable's own default.

## Change
A hash-locked receipt patches the donor's `Npc::getMaxSpeed` (enabled by `OPENOBLIVION_TES4_MOVEMENT=1`) so the player's ground speed uses the formula and the run and sneak stances directly. Swimming and levitation keep the existing paths.

## Oracle
Probe speeds against the formula's predictions, and one earlier private sample of the original walking down the Vilverin stairs (peak 117.3 units/s).

## Result
Worked for the modelled case. Desktop probe, same binary: walk 116.6, run 355.6, sneak 70.0 units/s with the weapon sheathed (with a weapon drawn: 106.0, 323.3, 63.6 walk, run, sneak). The original's walking peak of 117.3 is consistent with the sheathed walk. Not modelled: carried weight, changing attributes and skills, skill use, swim speed, jump height, sneak camera height. Other actors keep the borrowed speeds.

## Why
Inferred from a static read of the routine plus one consistent walking sample; the formula's run branch was never sampled in the original.

## Next
Sample the original's run and sneak speeds to confirm the run branch, then jump height and swimming. Publish the method and the rules, not settings tables.

## Unverified
Original run speed, sneak speed and jump; encumbrance and skill progression; phone feel.

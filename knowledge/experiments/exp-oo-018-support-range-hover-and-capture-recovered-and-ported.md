---
id: EXP-OO-018
title: "Recover the original's support range, hover and landing capture from drop trials and port them behind a switch"
project: openoblivion
result: worked
level: verified
why_level: verified
scope: build
status: final
date: 2026-10-08
agents: ["Claude Code (Sonnet 5.5)"]
about: [subsystem:player-controller, struct:bhkCharacterController, engine:openmw, technique:replay-oracle, technique:runtime-memory-sampler, technique:paired-same-binary-probe, technique:hash-locked-receipts, problem:tes4-movement-parity]
games: [game:oblivion]
tags: [support-range, hover, landing-capture, havok-character-proxy, drop-trial]
related: [EXP-OO-015, EXP-OO-019]
---

# Recover the original's support range, hover and landing capture from drop trials and port them behind a switch

## Symptom
After the airborne law was ported, two behaviours of the original were on record but unexplained: after a jump the state switched to ground 15 to 17 units above the final rest height and the hull then glided down for about a second, and a 38-unit stair flight never left the ground state. The port snapped the hull to the ground every step (the donor solver's 62-unit step-down), so landings and ledges looked nothing like the original.

## Hypothesis
One support range explains both: the controller is "supported" while the ground is within a fixed distance below it, and a supported controller does not accumulate gravity.

## Environment
The owner's retail game under Proton on an isolated display, software GL (about 21 updates/s at 800x600, 30 at 320x240), read-only 200 Hz sampler of the player's controller, input by scripted key events and console `player.setpos z`. Port: OpenMW donor solver, desktop probe (nominally 60 Hz physics) and a virtual Android device.

## Change
Placed the player 5 to 125 units above the base of a flight of stairs (a flat floor) and let it fall; bracketed the range with 13.0 to 15.1 units; replayed every update with the logged step time. Ported the law as a wrapper around the host movement solver (a new hash-locked receipt owning only the file that calls the solver), behind an opt-in switch.

## Oracle
Per-update replay of the original (position and velocity, residual 0.05 units) and, for the port, a unit test that feeds four recorded drops through the port's function, the desktop probe's jump and stair, ramp, wall and ceiling fixtures with the switch off and on, and the virtual device's jump log.

## Result
Supported while the ground is less than 2.0 Havok units (13.998 units) below rest (bracket 1.9717 to 2.0003). Supported on level ground: `vz = -g*dt` every update (no accumulation), so the hull sinks `g*dt^2` per update. The capturing update keeps its velocity; capture needs `vz <= 0`. The law replays at both frame rates. Port: rise unchanged, capture 9 to 14 units up, hover about a second at 60 Hz, stairs/ramp/wall/ceiling rows unchanged (steep contacts keep the host's handling); jumps on the virtual device rise the same with 0.045 s less air time.

## Why
Verified for the law on level ground. The stair flights show the same state with an accumulating velocity, so the hover rule is not the whole controller (see EXP-OO-019). The hull is a 40-unit-wide cone, which makes a stair nosing a steep contact.

## Next
Read the proxy's surface classification (supported, sliding, unsupported) from the executable to port the stair law; measure the original on a walkable ramp at 30 Hz or more; the owner's feel test of the hover and of walking downhill.

## Unverified
Behaviour at 60 fps (nothing above 30 Hz was recorded; the 60 Hz hover duration is a computation); walkable slopes: with the switch on the port rides about 14 units above a 28 degree ramp and is grounded 35% of the time, the original is unmeasured there. A 125-unit drop kills the level-1 player and returns the game to the main menu (restore health between trials). An exterior cell ran at 10 to 13 updates/s even at 320x240, too slow for any frame-rate-dependent measurement.

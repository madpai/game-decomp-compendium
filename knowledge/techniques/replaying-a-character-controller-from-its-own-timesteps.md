---
kind: technique
title: "Measuring an original game's character controller by replaying its own timesteps (live read-only sampler + per-update replay oracle)"
status: working
agents: ["Claude Code (Sonnet 5.5)"]
humans: []
date: 2026-10-06
links: ["https://github.com/madpai/OpenOblivion/blob/main/docs/research/TES4_AIRBORNE.md"]
tags: [character-controller, havok, memory-sampler, replay, oracle, jump, gravity, frame-rate, oblivion, proton]
---

# Replaying a character controller from its own timesteps

> Sample the running original at several times its update rate, collapse the samples into the game's own updates, then replay a candidate law over each update using the `dt` the game logged. If the law is right the residual is zero to rounding. It turned three guesses about Oblivion's jump (height, takeoff speed, integration order) and two about air control into exact statements with an hour of work, and it explained why every apex we had measured before disagreed with the formula.

## When to use it
You own an offline single-player game, you can run it unchanged (Proton is fine), and a port's movement does not feel like the original. Wall-clock curves of position over time are the wrong oracle when the original steps with its frame time: they differ run to run. Use this when the controller is a Havok/Bullet-style proxy with a state machine, and you can reach its state in memory.

## How
1. **Find the fields statically first.** From RTTI and a disassembly, find the controller class, its state classes and their update functions. Read what each update writes: a requested-state field, a current-state field, a velocity vector, the last step time, gravity scale, and the world pointer (gravity vector). Keep offsets private; publish the laws, not the addresses.
2. **Run the original isolated.** Own display (Xvfb container), own prefix and user folders, original controls. Never write to the process.
3. **Sample read-only at about 200 Hz** (5 ms) from a separate process: position, controller state, requested state, velocity, step time (`dt`), world gravity, the phantom centre. One `pread` of the whole controller block gives a consistent snapshot.
4. **Collapse to updates.** The game updates at its frame rate (28 Hz under software GL here); a new update is any change in (state, position, velocity). Keep each update's logged `dt`.
5. **Drive it with real input.** XTEST key down/up with timestamps from the same monotonic clock; log the events beside the samples. Console commands (`player.setpos`, `setav`) give repeatable starting points.
6. **Replay.** For each pair of consecutive updates apply the candidate law with the *second* update's own `dt` and compare position and velocity. Report maximum and mean residual per scenario.
7. **Only then port.** Put the law in the port with the same constants, drive the port with the same scenario and compare apex, speeds and the sequence of states.

## What it showed (Oblivion, Steam retail build)
- World gravity (0, 0, -73.575) Havok units/s^2; each update does `v -= g*dt` and then `x += v*dt` with the update's own `dt` (semi-implicit Euler), replayed with zero residual on 100+ airborne updates including one 166 ms frame. Consequence: jump height depends on frame rate (64.4 units at 35 ms steps, 66.8 at 60 Hz, 69.0 in the continuous limit), which is why measured apexes never equalled the formula's 69.
- Takeoff speed `sqrt(2 g h)` with `h = min + (max - min) * Acrobatics / 100`; first airborne velocity predicted to four decimals on three jumps.
- Air control: horizontal velocity relaxes toward the wanted ground velocity by `fJumpMoveBase + fJumpMoveMult * Acrobatics / 100` per update (0.015 for Acrobatics 5): exact on a jump from a walk.
- On the ground the controller keeps adding gravity each update and resets it on contact, so stairs are descended by free fall per tread without ever leaving the ground state.

## Gotchas
1. **Reading another process's memory is refused even for your own user** (Yama `ptrace_scope` 1) when the game is not a descendant of the sampler. Run the read-only sampler with the privileges your system needs, guard it with a check that the target's command line is the isolated reference, and never write.
2. **The first jump trial reads a lower apex than the formula** if there is a ceiling (the start corridor capped a jump at 32 units). Choose open space and look at `z` against a known ceiling before trusting an apex.
3. **A held jump or any wall-clock comparison hides the cause**: compare per update with the logged `dt`.
4. **Console toggling needs a held key.** A 28 fps game can miss a press shorter than a frame; send key down, wait 0.15 s, key up. Typed text is lost if the console is still closed (the letters become game input).
5. **`pkill -f '<pattern>'` kills the shell that contains the pattern** (and the tool call with it). Use `pgrep -f '[Z]:.*Oblivion.exe'` style patterns.
6. **Teleporting twice in a row once ended in the main menu** (probably a death and reload); relaunch and walk instead of chaining `setpos`.

7. **A port's own bookkeeping can break at a higher frame rate than the one you tested.** Add a one-line log of the quantity you matched (here each jump's rise) so the device reports it; the first phone run showed `rise 0` where the desktop showed 66.8 (EXP-OO-017).

## Verification
Replay residuals are exact on the recorded traces. Not verified: other Acrobatics values (the player's was 5), other frame rates, encumbrance, fatigue cost, creatures and NPCs, swimming, and the support range that decides when the ground state is kept or entered.

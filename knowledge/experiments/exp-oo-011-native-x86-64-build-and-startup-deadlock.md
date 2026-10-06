---
id: EXP-OO-011
title: "Native x86_64 build for the emulator gate, and the GL4ES/EGL start-up deadlock it exposed"
project: openoblivion
result: worked
level: verified
why_level: verified
scope: build
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5)"]
about: [problem:android-startup-deadlock, platform:android-x86_64-emulator, tech:gl4es, subsystem:android-port, technique:android-emulator-gate]
games: []
tags: [android, emulator, x86_64, deadlock, egl, dlopen, device-gate]
related: [EXP-OO-010]
---

# Native x86_64 build for the emulator gate, and the GL4ES/EGL start-up deadlock it exposed

## Symptom
After rebuilding for x86_64 (EXP-OO-010), launches intermittently never started: the process stayed alive at 0% CPU, the window list showed only the system "Splash Screen", the log stopped right after the activity's `onCreate`, and the activity manager reported "Launch timeout has expired". Three of four launches hung.

## Hypothesis
A lock-order deadlock: the main thread is inside `dlopen` of the GL4ES library (holding the linker lock) whose constructor calls `eglGetDisplay`, which waits for libEGL's driver-init mutex; the UI RenderThread holds that mutex while loading the driver and needs the linker lock.

## Environment
Android 16 x86_64 emulator with a userdebug image (`adb root` available), OpenOblivion rebuilt for x86_64 and overlaid into a copy of the phone APK, scripted gate with an explicit emulator serial.

## Change
Call `EGL14.eglGetDisplay(EGL_DEFAULT_DISPLAY)` on the main thread before the first `System.loadLibrary`, so the driver is initialised before GL4ES's constructor runs.

## Oracle
`debuggerd -b <pid>` printing every thread's native backtrace to show the lock cycle; launch outcomes before and after; a six-check gate (launcher ready, engine thread started, 20 s stable, drawn frame, menu opens, system BACK closes it).

## Result
Worked: three of four launches hung before the change and five of five started after it (small samples); the gate passes six of six on the Android 16 emulator. It checks Java, UI, input, Lua and engine logic, not arm64 code or phone speed.

## Why
Backtraces showed the cycle, and a slow emulator EGL start-up makes the race likely. Mechanism verified; real-phone prevalence unknown.

## Next
Package the next phone build with both Java fixes (this one and the Android back-key handling), extend the gate (other menus, a walk, a door, a conversation, frame timing), and confirm on a phone when phone testing resumes.

## Unverified
That phones hit this race (EGL starts faster there); sample sizes of 4 and 5 launches; any arm64-specific behaviour or performance.

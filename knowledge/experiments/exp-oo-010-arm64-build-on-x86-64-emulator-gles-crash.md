---
id: EXP-OO-010
title: "Run the arm64-only build on the stock x86_64 Android emulator and work around the GLES crash"
project: openoblivion
result: failed
level: verified
why_level: inferred
scope: build
status: final
date: 2026-10-06
agents: ["Claude Code (Sonnet 5.5)"]
about: [problem:android-emulator-gles-crash, platform:android-x86_64-emulator, platform:android-arm64, tech:opengl-es, tech:gl4es, subsystem:rendering-gl, subsystem:android-port]
games: []
tags: [android, emulator, arm64, gles, translation, sigsegv]
related: [EXP-OO-011]
---

# Run the arm64-only build on the stock x86_64 Android emulator and work around the GLES crash

## Symptom
The phone build installs and starts on an Android x86_64 emulator image (which lists arm64 in its ABI list through a translation layer) but crashes at scene start with SIGSEGV, fault address 0, in `libndk_translation_proxy_libGLESv2.so` on Android 14 or in a `berberis` trampoline on Android 16.

## Hypothesis
A fixable emulator configuration: the host GPU path, software rendering, or a newer system image would avoid the crash.

## Environment
Android 14 and Android 16 (API 36) google_apis x86_64 images, KVM, 4 GB RAM AVD, host GPU and software (`swiftshader_indirect`) rendering; OpenOblivion arm64-only APK rendering through GL4ES to GLES.

## Change
Varied the GPU mode (host, software) and the image version (14, 16) with the same APK.

## Oracle
Whether the app reaches a drawn frame; crash backtrace and fault address.

## Result
Failed in every combination: the crash persists at scene start.

## Why
Inferred. The translation layer's GLES proxy exposes entry points that the emulator's GPU library does not implement, leaving a null call target that GL4ES reaches during initialisation. The GPU mode and image version made no difference, which is consistent with a layer problem and not with a configuration problem.

## Next
Do not chase the function. Build the same engine source natively for x86_64, add `lib/x86_64` to a copy of the APK, and test with the scripted gate (EXP-OO-011).

## Unverified
Other emulator images, ARM-native hosts and real phones (which do not use this layer).

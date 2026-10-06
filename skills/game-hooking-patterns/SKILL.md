---
name: game-hooking-patterns
description: Patterns for modding or instrumenting a single-player/offline PC game at runtime - choosing the lightest route (data/asset edits, community loader API, managed patching, native hooks), getting code into a process (proxy DLL, ASI loader, mod loaders like BepInEx/UE4SS/REFramework/SKSE/OBSE/ModEngine2/me3), finding what to hook (RTTI, strings, signatures, singletons), writing safe hooks (calling conventions, main-thread tasks, vtable overrides), bridges to out-of-process tools, and the hard safety rules (no anti-cheat/DRM bypass, no online clients). Use when a task says mod, hook, detour, inject, DLL mod, script extender, overlay, trainer-like offline tooling, or "add a feature to a running game", and when studying fromsoftware-rs, universal-modder, Thief3 SDK or similar mod frameworks.
---

# Game hooking and runtime modding patterns

Prefer the lightest route that reaches the goal; every step down the list costs more maintenance per game update.

| Route | Use when | Examples |
|---|---|---|
| 1. Data/assets | the idea fits the game's data files | ESP/ESM plugins, Paradox scripts, JSON content packs, pak overrides, xdelta patches |
| 2. Loader API | the community already built a loader with hooks | tModLoader, SMAPI, BepInEx+Harmony, UE4SS Lua, REFramework Lua, SKSE/OBSE/xNVSE plugins, ModEngine2/me3, Fabric/Forge |
| 3. Managed patching | .NET/Mono/IL2CPP/Java, no API for the idea | Harmony prefix/postfix/transpiler, MonoMod, Mixin |
| 4. Native hooks | native C/C++ engine without a loader | proxy DLL + MinHook/SafetyHook/Detours/retour, signature scans |
| 5. Reimplement/decomp/recomp | total control or new platforms | see `engine-reimplementation`, `decomp-matching-workflow` |
Always search first: `python3 ../gamedecomp-library/scripts/hub.py prior-art "<game or engine>"` (decomp projects, agent field notes, engine playbook). If a loader exists, use it.

## Hard rules (non-negotiable; reasons in `references/safety-and-etiquette.md`)
1. Only games the user owns; single-player/offline or servers the user hosts.
2. Never inject into, attach to, or scan an online client protected by anti-cheat (EasyAntiCheat, BattlEye, Vanguard, VAC on official servers, Ricochet, ACE, Javelin). Offline modes launched through official or community-sanctioned means (e.g. ModEngine2/me3 launching an offline copy) are the norm; never online.
3. Never write cheats against other players; never bypass anti-cheat, DRM, or ownership checks. If a route needs a DRM-patched exe, stop and tell the user.
4. Back up saves/config first; kill processes by exact PID; bind bridges/debuggers/MCP to 127.0.0.1 with a token; ask before installing loaders into game folders, editing the registry, driving the user's mouse/keyboard, deleting anything, or publishing.
5. Do not publish game files, extracted assets, decompiled source, or retail offsets baked into shipped code. Publish your code and converters that read the user's own files.

## Getting code into the process (route 4)
- **Proxy DLL**: a DLL named like one the game loads from its own folder (`dinput8`, `version`, `winmm`, `dxgi`, `d3d9`, `xinput1_3`, `dwmapi`, `winhttp`) that forwards real exports and starts your code from `DllMain` on a new thread (do almost nothing under the loader lock). Check imports first (`re-binary-recon/scripts/pe_info.py --imports`).
- **Ultimate ASI Loader** loads `*.asi` plugins; many older games already ship it. Proton/Linux: `WINEDLLOVERRIDES="dinput8=n,b" %command%`.
- **Entry-point trick** (Thief 3 SDK): patch the exe's entry point so your init runs outside the loader lock; validate the build by PE timestamp and refuse to hook unknown builds; install a vectored exception handler that logs crashes.
- **Script extenders / loaders** per engine: see `references/loaders-by-engine.md`.

## Finding what to hook
1. Static recon (`re-binary-recon`): RTTI class/vtable map, strings -> functions, tables.
2. Resolve by *signature or RTTI*, not a hard-coded address: AOB patterns with wildcards; vtable slot by class + index; singletons by class name (`from-singleton` scans for FD4 singletons by binary regex with 10-15 ms first-use cost); keep a clear log when a pattern misses. Compute `module_base + RVA` under ASLR.
3. Prove it dynamically (hook to log arguments/returns, run the game, read the log) before building on it; mark facts static vs verified.

## Writing safe hooks
- Match the calling convention exactly (x86 `__thiscall` needs ECX `this`; x64 has one convention). A detour must return what the original returned (e.g. a vtable slot returning a pointer its caller uses directly).
- Detour via MinHook/SafetyHook/Detours/retour and call the original through the trampoline; mid-function hooks change registers at one instruction. IAT patches catch only the exe's own imports; inline hooks catch every caller.
- Engines expect most calls on their main thread: queue work and run it from a hooked per-frame function or the engine's task system (fromsoftware-rs registers Rust closures as recurring tasks in the game's own task runtime and cancels them on drop). Never block the main thread (no waiting on ffmpeg/network inside a hook).
- Overlay/UI: hook `IDXGISwapChain::Present`/`vkQueuePresentKHR` and draw Dear ImGui (hudhook is the Rust route); ReShade's add-on API offers present/draw/depth events without writing the hooks.
- Overriding C++ virtuals from another language: declare the vtable layout and provide implementations (`vtable-rs` macro; superclass/subclass checks verify RTTI before casting).
- Crashes: log with flushes; unhandled-exception filter writing a minidump.
- Game updates move everything: pin the supported build; document it; tests that assert resolved RVAs per supported build (fromsoftware-rs `rva_test`).

## Bridges (out-of-process helpers)
A thin in-game plugin captures events and talks over localhost (file drop, HTTP, WebSocket, named pipes, shared memory) to a heavier backend (AI NPCs, simulations, tools). Timestamp messages, tolerate different frame rates, add a watchdog. Start with a cube from process A drawn in B before real content. See `references/native-hooking-routes.md` for mashup/passthrough patterns.

## Verification (oracles)
Scripted repeatable scenario + game log + screenshot you actually look at; trace replay for ported logic; a circuit breaker (~3 identical failures then change approach); a journal file. `re-binary-recon/references/rtti-vtables-and-oracles.md`.

## Files
- `references/native-hooking-routes.md`: native route in depth, hook libraries, thread/overlay/input rules, passthrough/mashup patterns.
- `references/fromsoftware-rs-patterns.md`: what the best Rust game-hooking codebase does and why.
- `references/loaders-by-engine.md`: loaders, logs, and gotchas per engine (Unity, Unreal, RE Engine, FromSoft, RAGE, Bethesda, Source, Java, .NET).
- `references/safety-and-etiquette.md`: the rules with reasons and the red-line cases.

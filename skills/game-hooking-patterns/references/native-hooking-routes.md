# Native hooking routes in depth (single-player/offline only)

Condensed from universal-modder's `native.md`, `big-frameworks.md` and `mashup-mods` skill (MIT), the Thief 3 SDK docs (MIT) and fromsoftware-rs.

## 1. Get code into the process
- Proxy DLL (names the game loads from its own folder: `version.dll`, `dinput8.dll`, `winmm.dll`, `dxgi.dll`, `d3d9.dll`, `xinput1_3.dll`, `dwmapi.dll`, `winhttp.dll`): forward the real exports; run your init on a new thread from `DllMain`.
- Ultimate ASI Loader (ThirteenAG): loads `*.asi` (renamed DLL) from the game or `scripts/` folder.
- Launcher that starts the game suspended and injects: last resort.
- Thief 3 SDK specifics worth copying: loads as `System/dinput8.dll`; patches the exe entry point to start outside the loader lock; hooks `PeekMessageA` for a per-frame callback, `ExitProcess`/`TerminateProcess` for shutdown, the engine's log writer for log capture; validates object layout at runtime before declaring the engine ready; refuses unknown PE timestamps; mods are DLLs exporting `T3Mod_Init(const Api*)` loaded in a listed order; the API is plain C `__cdecl` and only grows (check `api->size`).

## 2. Find what to hook
Static: strings and imports, RTTI, signatures. Dynamic (offline, single-player): Cheat Engine value scans -> "what writes this" -> struct -> owner; x64dbg breakpoints; ReClass.NET; Frida. Graphics: RenderDoc captures reveal view/projection matrices in constant buffers and which pass draws what.

## 3. Hook
- Libraries: MinHook, SafetyHook (mid-function `MidHook`), Microsoft Detours, `retour`/`detour` (Rust), `ilhook`.
- IAT patches for Windows-DLL imports (catch the exe's calls only); inline trampolines for code inside the exe and for D3D device methods found through vtables (`IDirect3DDevice8` cursor methods at slots 10/11/12 in the Thief 3 notes).
- Hook a vtable slot either by reading the function pointer and detouring the function (catches every caller) or by overwriting the slot (affects only that vtable).
- COM interfaces (Direct3D): declare slots as `virtual int __stdcall`; `this` is pushed last; no ECX.
- Keep hooks tiny; heavy work on your own thread or out of process; never wait on I/O in the main thread.

## 4. Draw and interact
- Overlay: hook `Present` (D3D11/12), `vkQueuePresentKHR` (Vulkan); Dear ImGui; Kiero helps find the vtable; ReShade add-on API gives present/draw/depth events.
- Inject 3D content into the game's own pass: use its view-projection matrices and depth buffer; or spawn host-native objects so lighting/shadows apply.
- Input: hook the game's input handling or raw input/XInput; route input to one process at a time in two-process designs.

## 5. Mashup and passthrough patterns (universal-modder `mashup-mods`)
1. *Port content*: recreate a guest enemy/weapon as host content (read exact numbers from the guest; convert assets on the user's machine at install time, never ship them).
2. *Passthrough*: two processes exchange state over localhost (shared-memory ring buffer, UDP/pipes, JSON lines/HTTP; GPU frames via DXGI shared handles/Vulkan external memory/Spout2). Host plugin draws guest geometry in the host's pass; host collision flows back as colliders; timestamps and watchdogs; start with one cube.
3. *Embed a decomp as a library* (libsm64 pattern: feed collision and input, get state and mesh).
4. *Reimplement then fuse* with a scriptable runtime as the oracle and an evidence journal ("knowledge not in an artifact does not exist").
5. *Headless guest rules, host as the view* for number-driven guests: pure simulation at the guest's own step rate; mirror entities only where the player must touch; batched records for high-volume objects; every UI button is a command.
Verification: headless bench first, then scripted real-world run, then human run in the real setup; list what the benches cannot see.

## 6. Pitfalls checklist
ASLR (use base + RVA); main-thread requirement; crashes (flushed log + minidump); game update (pin build); anti-cheat (stop); single-instance mutexes and crash reporters (clear by PID); Proton: `WINEDLLOVERRIDES="<dll>=n,b" %command%`; Windows screenshot APIs may freeze under ReShade/independent-flip (prove the capture is live).

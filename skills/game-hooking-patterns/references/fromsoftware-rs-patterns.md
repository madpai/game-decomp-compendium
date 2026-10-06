# What fromsoftware-rs does (and why to copy it)

Repository: `vswarte/fromsoftware-rs` (MIT/Apache-2.0), plus companions `tremwil/vtable-rs`, `dasaav-dsv/from-singleton`, `dasaav-dsv/liber`. Read in the local clone corpus (crates `shared`, `eldenring`, `darksouls3`, `sekiro`, `nightreign`; `tools/binary-mapper`, `tools/param-generator`; `examples/`; `tests/`). The games are x64 MSVC with RTTI; the techniques apply to any similar engine in single-player/offline modding. The repo also contains an anti-tamper code-restoration disabler for a specific protection; that is out of scope here and not documented by this hub.

## Layout
- One crate per game with `#[repr(C)]` structs mirroring engine classes, plus a `shared` crate for what the games have in common (singleton lookup, task runtime, STL types, allocator bridge).
- Docs on every struct field mark confidence; offsets are validated by `size_of` assertions and tests.
- Mods are `cdylib` DLLs: `DllMain` spawns a thread, waits for the game to be ready, installs hooks (`ilhook`/`retour`), draws UI with `hudhook`, registers per-frame work as engine tasks.

## Patterns worth stealing
1. **RTTI-derived structure layouts**: names and inheritance come from the binary (`rtti_scan.py` produces the same data); a `Superclass`/`Subclass` trait pair casts safely by checking RTTI at runtime instead of trusting a pointer.
2. **Singleton access by name**: `FromStatic`/`FromSingleton` traits resolve a singleton instance from the class's registration data with a binary-regex scan (lazy, 10-15 ms once), instead of hard-coded addresses per patch.
3. **Binary mapper (AOB -> RVA)**: a TOML profile of `[[patterns]] pattern="48 8b ?? ... $ { ' }" captures=["NAME"]` (pelite pattern language: `'` saves the cursor as a capture, `$` follows a rel32 displacement and `{ ... }` continues matching at the followed address, so `e8 $ { ' }` captures a call target) and `[[vmts]] class="Ns::Class" captures={ NAME = 27 }` (virtual method index via RTTI; the RVA is the function, not the vtable slot). It drives `pelite`'s scanner, emits a Rust `RvaBundle`, runs per game/region exe via env vars `MAPPER_{GAME}_{REGION}_EXE`. Regression tests assert the RVAs for each supported build.
4. **Param structs generated from definitions**: `tools/param-generator` turns community param-definition XML (Paramdex) into Rust structs, so thousands of data tables stay in sync with the game.
5. **Main-thread task registration**: `SharedTaskImpExt::run_recurring(closure, group)` registers a Rust closure in the game's own task system and returns a handle whose `Drop` cancels it. Do game-state work there, not on your own thread.
6. **Engine allocator awareness**: objects owned by the engine must be allocated/freed through the game's allocator (`game_allocator.rs`, `owned_pointer.rs`), otherwise you corrupt its heap.
7. **MSVC STL layouts** (`std::string`/vector/map internals) re-declared in Rust so engine containers can be read safely (small-string optimisation, capacity/size field order are version-specific).
8. **vtable-rs**: `#[vtable] trait ObjVmt { fn method(&self, arg: u32) -> u32; }` plus `VPtr<dyn ObjVmt, Self>` lets Rust objects be passed to C++ expecting an abstract class, with single inheritance via trait bounds. Calling `destructor` from Rust is unsound: only C++ should call it.
9. **Examples as documentation**: tiny mods (debug line, apply status effect, spawn asset, invoke scripting from a hook, present an action button) each prove one capability end to end.
10. **Multi-game, multi-region discipline**: per-game crates, per-region exe inputs to the mapper, explicit tested versions in each library's README (`from-singleton` lists DS3 1.15.0/1.15.2, Sekiro 1.06, ER 1.16, AC6 1.07.1).

## Takeaways for any Bethesda/Halo/Source project
- Get class names and vtables from RTTI first; anchor everything on them.
- Build the resolver (signatures/RTTI/singletons) and its regression test before the first feature.
- Keep the resolver data outside the code that uses it (profile file), versioned per game build.
- Use the engine's own scheduling and allocator.

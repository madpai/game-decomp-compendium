# Signatures, versioning and the tool menu

## Addresses, RVAs, signatures
- **Fixed-base, no relocations** (old x86 games): VAs are stable for one exact build. Guard with the PE timestamp (Thief 3's SDK refuses to hook any build other than its known timestamp).
- **ASLR/relocatable**: compute `module_base + RVA` at runtime; never hard-code absolute addresses.
- **Signatures** (AOB with wildcards for operands that move) survive recompiles; keep a fallback that logs clearly when a pattern is not found. fromsoftware-rs ships a *binary mapper*: a TOML profile of named AOB patterns resolves to RVAs for a game build and an `rva_test` asserts the resolved values for every supported build, so a patch that breaks a pattern fails CI instead of crashing players.
- **Address Library style** (Bethesda SKSE/F4SE): version-independent function IDs resolved per game build.
- **RTTI/singleton lookup**: find objects by class name at runtime (`from-singleton`) instead of by address.
- **Immediate patches**: changing one operand constant (e.g. a minimum frame step) needs only a byte check + write; guard by comparing the existing bytes and leaving the game untouched if they differ.

## pelite's pattern language (richer than plain AOB)
From pelite's `pattern/syntax.md` (Rust crate; the `binary-mapper` tool drives it): `48 8B C1` exact bytes; `?` wildcard byte; `A0/F8` masked byte (`b & F8 == A0 & F8`); `"text"00` string bytes; `skip(n)`/`skip(-n)`/`skip(ptr)` move the cursor; `scan(n)` try the rest at offsets 0..n; `@4` require 16-byte alignment; **`$`/`rel32`, `%`/`rel8`, `*`/`ptr` follow a relative or absolute reference and `{ ... }` continues matching at the target**; **`'`/`save` stores the cursor as a capture** (`save[3]`, `seek[3]`, `check[3]` use explicit slots); `u4`/`i1` read values into slots; alternatives are supported. Example: `83 cb 02 89 5c 24 20 48 8d 54 24 38 e8 $ { ' }` captures the call target after a distinctive prologue. Use it when a plain wildcard signature is too fragile (follow a call, then match the callee's first bytes).

## Import-table vs inline hooks (for later; offline/single-player only)
IAT patching catches the exe's own calls to Windows DLL functions with no code change; inline hooks (MinHook/SafetyHook/Detours/retour) are required for code inside the exe or for calls made by other modules. See `game-hooking-patterns`.

## Tool menu
| Need | Tools |
|---|---|
| Decompile/disassemble | Ghidra (headless + MCP: GhidraMCP, pyghidra-mcp, ReVa), IDA (official MCP / ida-pro-mcp), Binary Ninja, radare2/rizin |
| Decode/assemble programmatically | iced-x86 (Rust/.NET/Python/JS/Lua; instruction info: registers, memory, flow), Capstone, Zydis |
| Parse binaries | `pelite` (PE, Rust, pattern scanner, CLI), `goblin`, `object` (also writes COFF/ELF/PE), `gimli` (DWARF), LIEF, pefile |
| Live inspection (offline single-player only) | x64dbg, Cheat Engine, ReClass.NET, Frida (+frida-rust), UnityExplorer, UE4SS live view |
| Graphics | RenderDoc (find view/projection matrices, depth, render targets) |
| Unity | ILSpy/dnSpyEx (Mono), Il2CppDumper, Cpp2IL, AssetRipper, UnityPy |
| Unreal | UE4SS dumpers, Dumper-7, FModel, UAssetAPI |
| Name demangling | `undname`/`c++filt`, `cwdemangle` (CodeWarrior), `rustfilt` |
| Format RE | hex editors, Kaitai Struct (`.ksy` specs: isle uses them), `binrw`/Construct, QuickBMS archives, XeNTaX/ZenHAX archives for historical format knowledge |

## Making Ghidra/IDA useful for agents
Prefer code-capable MCP tools (run a script) over hundreds of micro-tools; keep a headless script set: `Decompile.java <addr> [refs:<addr>]`, `Disassemble.java <addr>[+n]`, `names` (apply `symbols.txt`), `bootstrap`. Cache decompiles. Feed names back to a single source-of-truth file (`symbols.txt`/`symbols.csv`) and re-apply, so renames in the repo and in the database cannot drift. Treat decompiler output as a hypothesis (it guesses types and signedness); confirm against disassembly and callers; agents confidently misidentify things, so confirm dynamically before building on a guess.

## Rust RE crates worth knowing (from the catalog)
`pelite` (PE + patterns), `goblin`, `object`, `gimli`, `iced-x86`, `binrw` (declarative parsers), `retour` (detours), `frida-rust`, `memflow` (out-of-process introspection; not covered here), `vtable-rs` (C++ vtable layouts), `from-singleton`, `bsa-rs` (Bethesda archives), `esplugin`/`libloadorder` (GPL-3.0).

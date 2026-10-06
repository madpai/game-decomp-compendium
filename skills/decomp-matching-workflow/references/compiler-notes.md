# Compiler and architecture notes for matching

Paraphrased and condensed from: Thief 3's verified MSVC 7.1 `CHEATSHEET.md` and worker codegen section (MIT), BW1/LEGOLAND notes (MSVC 6), decompedia compiler pages (MWCC, GCC, IDO) and guides (assembly patterns, `$gp`, line numbers, maspsx). These are leads to *test with your own compiler*, not facts to assume: flags, versions and forks change output. Add an idiom to a project cheat sheet only after reproducing it with the project's compiler.

## Identify the compiler first
| Signal | Meaning |
|---|---|
| PE Rich header product ids / builds (`re-binary-recon/scripts/pe_info.py`) | which MSVC cl/link built the objects (a DLL can differ from its EXE: AVP2's renderer used VC6 RTM, the engine VC6 SP5 + Processor Pack) |
| `.comment` section string like `MW MIPS C Compiler (2.4.1.01)`; a `main` section merging text/data/rodata; overlay headers starting `MWo` | Metrowerks (PS2). GameCube/Wii MWCC has no `.comment` |
| DWARF 1 `.debug` (PS2 MWCC, old GCC), DWARF 2 (GC/Wii MWCC >= 3.0), STABS | debug info may exist in the retail binary or a demo/beta build |
| PSY-Q libraries, SN Systems strings | PS1/PS2 GCC 2.x forks |
| `__ehhandler$`, `fs:[0]` frame chain, `___CxxFrameHandler` | MSVC `/GX` exception handling (see below) |
| `__ftol2`, `__real@` constants, `fnstsw ax; test ah,5` | MSVC x87 float codegen |
Wrong compiler or flags = unwinnable diffs; spend the time to get it right before matching a single function.

## MSVC x86 (6.0 / 7.1) idioms
Observed with `cl 13.10.3077 /O2 /GX /GR- /MT` (Thief 3) unless noted.
- **Same-TU inlining**: with `/O2` any small function whose body is visible in the translation unit can be inlined, even if defined after its caller. Scratch/test files must *declare* callees, never define them; a `call` in the target must stay a call.
- **No-op rewrites** (switching wastes attempts): `s->x + s->y` vs `s->y + s->x`; `if (a) return 1; return 0;` vs `return a != 0;` vs a `bool` return; `for` vs `while`.
- **Constant arithmetic**: `x*2` shl; `x*3/5/9` lea; `x*6` lea then shl; `x*7` imul; `x+1` inc; `x-3` add 0xfffffffd; signed `x/2` = cdq, sub, sar; unsigned shr; `x/3` signed = `mov eax,0x55555556; imul ecx; mov eax,edx; shr eax,0x1f; add eax,edx`.
- **Floats**: every float constant the FPU loads comes from a `__real@xxxxxxxx` pool entry (even 0 and 1); a constant that is only *stored* is a `mov` of its bits. `(int)f` = `fld; jmp __ftol2` (tail call). `a < b` = `fld a; fcomp b; fnstsw ax; test ah,0x5`; `<=` tests 0x41. Float32 vs float64 constants matter (`0.2f != 0.2`).
- **Calling conventions**: `__thiscall` = `this` in ECX, callee pops args (`ret N`); `__fastcall` = first two args ECX/EDX, decorated `YI`; `__stdcall` = `ret N`, decorated `YG`; `__cdecl` = caller cleans (`add esp,N`). Hooking a thiscall function requires a replacement with the same convention (a plain C function receives garbage `this`).
- **Virtuals**: virtual call `mov eax,[ecx]; call [eax+4*slot]`; `delete p` through a virtual destructor calls slot 0 with arg 1 (`test ecx,ecx; je; mov eax,[ecx]; push 1; call [eax]`). A direct call to a function that is virtual needs a qualified call (`Base::F()`), else it dispatches through the vtable. An inlined base constructor stores the base vtable first and the derived later: write both stores.
- **Tail calls**: a last call forwarding the caller's own args becomes `jmp`. `mov eax,ecx` at entry = method returns `this`. A `ret N` counts every argument, used or not. `sete al; push eax` with no preceding `xor eax,eax` = `bool` parameter. `movzx eax,al` after a bool-returning call = caller returns int.
- **Struct/array**: 32-byte struct copy = `rep movsd`; small fixed loops unroll; dense switch = `cmp; ja default; jmp [eax*4+table]` with the table after the function, sparse switch = compare tree. `memset(&field,0,size)` inline = `xor ecx,ecx` then unrolled `mov [edx+k],ecx`. 1-bit bitfield store uses the `xor/and/xor` mask pattern: declare a bitfield, do not hand-write it.
- **Exception handling (/GX)**: a function with destructible locals gets `push -1; push __ehhandler$...; mov eax,fs:[0]; push eax; mov fs:[0],esp` and state stores (`dword` first/final `-1`, `byte` in between); unwind funclets and the handler land in `.text$x`, tables in `.xdata$x`. **Declaration order = construction order = stack slot order**: if rows differ only by which slot holds which object, swap declarations.
- **Globals**: `extern void* DAT_x[];` for an address used as an immediate (a scalar `extern void* DAT_x;` would load through it); static locals live in `.bss`; `mov ecx,[Global]` before a call ecx is otherwise unused for means `Global->Method()`; a call on a global *object* is `mov ecx, offset Global`.
- **Compiler-generated, not source**: this-adjustor thunks (`add ecx,N; jmp`), deleting destructors (`test byte ptr [esp+8],1`...), global initialisers (ctor call then `atexit`), implicit ctors/dtors (match only with the function that emits them), InternalConstructor-style template instantiations. Defer, never hand-write.
- **MSVC 6 specifics** (BW1/LEGOLAND/AVP2): header dependencies are not tracked by wrapper scripts (delete objects after header edits); the c2.dll inliner has a per-function budget with a ~40 IL-unit free threshold; equal-cost x87 operand order is a tie-break tied to prior IL volume.
- **Library code**: STL/CRT instantiations inside game objects are not game code; link prebuilt library objects or mark them as library matches rather than hand-writing them (AVP2's `libmatch.py` identifies VC6 CRT/WONAPI objects).

## Metrowerks (MWCC; GameCube/Wii/PS2/DS/Xbox 360 variants)
- Proprietary, so decomps ship a pinned compiler set run under `wibo`/`wine`; a Mac MWCC decompilation exists.
- Float constants are not de-duplicated across TUs by the linker: repeated `0.0f`/`1.0f` mark TU starts (a splitting hint).
- GC int<->float conversion: `fctiwz` + stack round trip for float->int; `xoris/stw/lfd/fsubs` against the magic double `0x4330000080000000` for int->float.
- Struct copies: <=64 bytes copied member-wise (or via FPRs when 8-byte aligned), larger use memcpy-style loops.
- **Interprocedural optimisation within a TU** (observed on PS2 MWCC): if a callee is `static` in the same TU the compiler can prove it leaves registers intact and omits save/restore moves; the same code with a non-static callee needs them. A function that "cannot" match alone may need its callee's linkage fixed.
- PS2 MWCC -O0: `if (0xFF < tmp)` vs `if (tmp >= 0x100)` changes whether `at` is used for the compare; `%= 0x20` emits `li` then `andi` overwriting it.

## GCC family (N64 KMC/2.7.x/2.8.1, PSY-Q 2.6-2.8, PS2 SN 2.9x-3.2, GBA agbcc)
- Versions are forks; patterns differ per game. Known: N64 2.7.2 (KMC), 2.8.1 (Paper Mario), SN64; PSX PSY-Q (GCC 2.x); PS2 EE 2.9.x/2.95.x/2.96/3.2, IOP 2.8/2.95.
- Load/store combining, `bnel` "likely" branches, delay-slot NOPs (PS2 float literals), `MULT_HI` division by constants, `sltiu` range checks (`x-0xE9 < 0xD` for `0xE9<=x<=0xF5`), `andi v0,a1,0xfffe` for index/2 with 2-byte stride, signed div by power of two (`bgez; addiu +(d-1); sra`).
- **`$gp` (MIPS small data)**: `-G<n>` (GCC) / `-sdatathreshold n` (MWCC) place objects <= n bytes in `.sdata/.sbss` addressed via `$gp` in one instruction. GCC uses `$gp` only for variables defined in the current TU (extern ones fall back to `lui+lw`); MWCC also uses it for externs in range. A variable accessed both ways inside one file hints that the file was originally split. `$gp` is initialised in the entry point (`lui $gp,hi; addiu $gp,$gp,lo`).
- PS1: `maspsx` post-processes GCC output to mimic PSY-Q's ASPSX so modern GNU `as` can emit ELF objects (PSY-Q object format is proprietary and conversion is lossy).
- Line numbers in target asm (decomp.me/objdiff): `.loc <file> <line>` before the instructions, or STABS (`.stabs "file.C",100,0,4,.Ltext0` then `.stabn 68,0,<line>,<label>-<func>`), when debug info is available.

## IDO (SGI, N64)
Only IDO 5.3 and 7.1 were used for N64. Runs on IRIX; community uses a statically recompiled build (`ido-static-recomp`) instead of QEMU; an IDO matching decompilation (partly Pascal) is underway. Examples: SM64, OoT/MM (mostly 7.1), Banjo, DK64, Conker, Pokemon Snap (7.1), Snowboard Kids (5.3).

## Tools that appear around compilers
`decomp-permuter` (random source mutations toward a match), `m2c` (MIPS/PPC to C first pass), `spimdisasm` (MIPS disassembly), `splat` (split ROMs), `asm-differ`/`objdiff`, `decomp.me` scratches (share a function + compiler preset), `cwdemangle` (CodeWarrior mangled names), `wibo` (run Windows compilers on Linux).

---
name: decomp-matching-workflow
description: How to run a matching (byte-for-byte) decompilation or a function-by-function reverse-engineering effort, alone or with many agents. Use whenever a task involves decomp projects, objdiff, asm-differ, dtk, splat, reccmp, decomp.me, decomp.dev, symbols.txt/splits.txt, matching a function to original compiler output, naming functions in a binary, recovering original compiler/flags, or orchestrating parallel agents over thousands of RE work items (claims, deferrals, sweeps). Also use it to decide whether matching is even the right goal for a project (porting, modding or documenting usually needs less). Covers the toolchain map, the per-function loop, experiment discipline, agent-swarm economics, verification rules and legal posture.
---

# Matching decompilation workflow

A matching decomp rewrites a game's source so the *original compiler* regenerates the *original bytes*. The reason people do it: byte equality is an objective oracle, so every claim ("this function is `Actor::Update`") is checkable by machine, and wrong guesses cannot hide. Even if you never intend to match, the same discipline (evidence levels, oracles, ledgers) makes any reverse-engineering effort more reliable.

## 0. Pick the goal before picking tools

| Goal | What you need | Matching required? |
|---|---|---|
| Understand/port one subsystem (e.g. OpenOblivion's script runtime) | Names, struct layouts, behaviour traced from the binary; tests against real data | No. Use `re-binary-recon`, record evidence levels |
| Mod/hook a shipped game | Addresses or signatures for one build, class layouts | No. See `game-hooking-patterns` |
| Rebuild the executable from source (preservation, shiftable mods, native ports) | Compiler + flags + per-TU splits + matched functions | Yes |
| Port to new platforms with readable source | Matching is the gold standard but "equivalent" source verified by behaviour tests also works (see `engine-reimplementation`) | Optional |

If the answer is the first two rows, stop reading this skill after sections 2 and 5 and go to the sibling skills. Matching an entire engine is months of work; extracting the 5% you need is days.

## 1. The shape of every matching project

1. **Target binary** (never committed; identified by hash/PE timestamp).
2. **Splits**: where each original source file (translation unit) begins and ends in `.text/.data/.rdata/.bss`, plus **symbols** (names, sizes, types). Tools: `dtk` (GC/Wii/Xbox 360 ELF/DOL/XEX), `splat` (N64/PS1/PS2/GBA), hand-written `splits.txt`/`symbols.txt` (dtk format: `name = .text:0xADDR; // type:function size:0x.. scope:global`), Ghidra exports for x86.
3. **Build** the C/C++ with the *original compiler* (MWCC, MSVC 6/7.1/8, IDO, GCC/PSY-Q forks, SN, Watcom, clang for Switch). On Linux, Windows compilers run under `wibo` or `wine`. Pin compiler + flags in `configure.py` (generates `build.ninja` + `objdiff.json`).
4. **Compare** each compiled object to the target object with `objdiff` (GUI/CLI/WASM) or `asm-differ`/`diff.py`. Per-symbol percentages feed `decomp.dev` progress reports; `reccmp` does the equivalent for x86 PE with address-annotated source (`// FUNCTION: GAME 0x00401000`).
5. **Link** matched objects and compare the executable hash/sha1 (`build.sha1`, ReproBit-style checks) so "matches" is proven at the file level, not just per function.

Read `references/pipeline-and-files.md` for the exact file formats and commands, and `references/platform-playbook.md` for what each platform's projects use (computed from 220 projects).

## 2. The per-function loop (human or agent)

1. **Get context**: target asm, callees/globals referenced (with names), similar already-matched functions, class layout so far, any debug strings.
2. **Draft** plausible original source (what a programmer would have written; never transliterate registers). Decompilers (Ghidra, m2c for MIPS/PPC) give a starting point, not an answer.
3. **Compile with the pinned compiler, diff, read the diff.** Before the next edit, *classify* the difference (this single habit separates effective from thrashing attempts):
   - different instructions/operands/offsets/callees → the source is wrong (types, expression, field, callee);
   - same instructions, registers or order swapped → compiler tie-break; try at most two unrelated rewrites, then defer;
   - a helper inlined on only one side → inline-budget problem (see `references/experiment-discipline.md`);
   - only a name/signature differs → naming conflict for the lead, not a codegen problem;
   - offset/size/vtable slot you cannot know → missing evidence; defer with what would unblock it.
4. **Stop on a budget**: ~5 attempts for tiny functions, 8-10 for large; 3-4 consecutive attempts with no better score means defer. Measured at Thief 3: 77% of functions matched on attempt 1, then 65%, 37%, 39%, 23% of those reaching attempts 2-5, so late attempts are expensive and rarely pay.
5. **Record**: accepted (with the source), or deferred with a one-line blocker beginning with a slug (`tiebreak:`, `inline:`, `layout:`, `vtable:`, `signature:`, `name-conflict:`, `library:`, `engine:`, `compiler-generated:`, `asm:`). Deferring is a normal outcome; the best attempt is kept for a second pass.

## 3. Hard rules that keep matches honest

- No inline asm, `naked`, `goto`, codegen `#pragma`, literal exe addresses, `volatile` to keep a store, variables named after registers, data declared as functions to take their address, or invented class names. These all passed byte gates in past projects and were rejected at review. A match that is not plausible source is a fake match.
- Library code (CRT, STL instantiations, D3DX, Havok, engine middleware) and compiler-generated code (adjustor thunks, deleting destructors, EH funclets, global initialisers) are not "game code": exclude them from the queue or link prebuilt objects; do not hand-write them to chase percentage.
- Treat decompiler signatures and function boundaries as hypotheses; corroborate with call sites, vtable slots, other-platform symbols (Mac CodeWarrior symbols were ground truth for BW1), debug strings, beta/debug builds.
- State the comparison mode when reporting: report-match vs strict-object-match (relocation identities) vs resolved-byte match. A rounded 100.0% is not proof. Never add padding or undo symbol recovery to restore a percentage.
- Header changes can change codegen (TU-local constants, static initialisers, inlining). Delete dependent objects after header edits if the build has no header dependency tracking; verify header consumers.
- Evidence levels in notes: **static** (inferred from code/strings) vs **verified** (observed at runtime or confirmed by an independent second source). Do not upgrade a guess without an independent confirmation.

## 4. Scaling out with agents

Read `references/agent-swarm-playbook.md` before launching more than two workers. Core ideas: one lead owns everything shared (headers, symbols, splits, integration) and workers write only scratch files; a claim queue prevents duplicate work; a strict accept gate (compile + diff + rulers) is the only way a function counts as matched; workers return one JSON line; cheaper models take tiny functions, stronger models take big ones; sweep and review at checkpoints (grep for the cheat patterns above). `scripts/claimq.py` is a dependency-free claim/ledger implementation you can drop into any bulk-RE task (naming, signature recovery, matching).

## 5. Where the time goes (and how to save it)

- Setup (splits/symbols/compiler identification) dominates early; it is worth building a *library-matcher* so CRT/middleware code is marked done automatically (AVP2 identifies VC6 CRT objects and counts them matched).
- Find the compiler first: Rich header product ids in the PE (`re-binary-recon/scripts/pe_info.py`), `.comment` strings, compiler-specific idioms (`references/compiler-notes.md`). Wrong compiler = unwinnable diffs.
- Prefer a beta/debug/other-platform build with symbols as ground truth when one exists (Halo CEA PDBs, BW1 Mac symbols, FNV Xbox 360 MemDebug, LEGO Island beta).
- Families of byte-identical functions that differ only in referenced symbols should be matched once and stamped (Thief 3: 68 wrappers from one member).
- Keep progress honest and public via `decomp.dev` reports (objdiff `report` output); it also gives PR comments with deltas.

## 6. Legal and community posture

Source-only repositories; the user supplies the binary; no assets, no raw decompiler output or disassembly, no leaked SDK/source material (several projects forbid AI use partly because models may have seen leaks). Many decomp projects prohibit AI-generated contributions or even agent indexing; check `gamedecomp-library` (`query.py --ai human-only`) and the project's CONTRIBUTING, never open issues/PRs for the user unasked, and disclose AI assistance where policy asks for it. See `references/legal-and-etiquette.md`.

## Files

- `references/pipeline-and-files.md`: file formats (symbols.txt, splits.txt, objdiff.json, reccmp-project.yml, config.yml), command cheat sheet, reccmp annotations, ReproBit.
- `references/agent-swarm-playbook.md`: orchestration design with measured numbers.
- `references/experiment-discipline.md`: mindset, classification table, inline-budget and tie-break handling, baselines/regression checks.
- `references/compiler-notes.md`: MSVC x86, MWCC, GCC/PSY-Q/SN, IDO idioms; `$gp`; line numbers; shiftability.
- `references/platform-playbook.md`: toolchain by platform from the corpus.
- `references/legal-and-etiquette.md`: licences, policies, what never to commit.
- `scripts/claimq.py`: atomic claim queue + ledger for parallel workers.

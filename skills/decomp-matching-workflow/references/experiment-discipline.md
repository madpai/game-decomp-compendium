# Experiment discipline for matching work

Distilled from BW1's AGENTS.md (the most explicit statement of method in the corpus), Thief 3's worker protocol, LEGOLAND/AVP2 notes and decompedia. Paraphrased; read the originals in the clones for the full text.

## Mindset
- The work is getting into the original developers' heads using only evidence: binary, linker map, debug strings, compiler behaviour, other-platform symbols. Doubt every assumption (names, structure, control flow, even "looks right") and commit only when evidence is overwhelming.
- When a hard call lacks evidence, **leave it non-matching, leave a TODO, move on**. Evidence usually arrives later (a neighbouring function, a pattern in another TU, a debug string). A premature wrong commitment is technical debt harder to undo than a TODO.
- Final goal is *readable, modifiable* source, not merely a matching binary. Judgement calls that need a human (naming disputes, architecture, accepting a "fakematch") are deferred to the human.

## Classify before you experiment (one line per attempt)
| Observed difference | Class | Procedure |
|---|---|---|
| Different instructions, operands, offsets, callees | real source difference | fix expression/types/field/callee; read context packet again |
| Same instructions, registers or order swapped | tie-break / scheduling | at most two unrelated rewrites (statement order, a temp), then defer `tiebreak:` |
| Helper inlined on one side only | inline budget | measure helper IL size; change cost without changing bytes (ternary vs if, compound assignment); do not use `__forceinline` or invented layouts |
| Only name/signature differs (score 99.9+) | naming | defer `name-conflict:` for the lead's naming pass |
| Unknown offset/size/vtable slot | missing evidence | defer `layout:`/`vtable:` with what would settle it |
| Target looks hand-written asm | out of scope | defer `asm:` immediately |

Rules of thumb that cost others weeks:
- *Prove that a knob moves the output before sweeping it.* A 5,000-build sweep over knobs that never touch the differing instructions finds nothing.
- *Before trying another variant, name the assembly difference it is meant to explain.* If variants just shuffle registers or move the mismatch elsewhere, keep the clearest supported version and document the unresolved cause.
- *Rank assumptions by evidence*: other-platform symbols and call sets across all units outrank guessed shapes of fabricated or hand-expanded functions. When a model cannot fit every caller, doubt the weakest-evidence caller before rewriting shared headers.
- *Bound the search and escalate early.* Once a residual is shown to be a compiler tie-break (equal-cost x87 operand order inside inlined bodies, which depends on how much IL the inliner built earlier in the function), stop hunting; ask whether to accept a fakematch. Reverse-engineering the tie-break rule has not paid off.
- Identical-after-rewrite pairs waste attempts: `a+b` vs `b+a`, `if(a) return 1; return 0;` vs `return a != 0;`, `for` vs `while` (MSVC 7.1 verified). The harness should say "same compiled code as attempt N".

## Inline budget (MSVC 6 c2.dll, BW1 research)
The inliner has a per-function budget; helpers up to ~40 IL units are "free"; nested budget shares exist. Tools to build: `size` (exact IL size of one inline call using the unit's real compile command), `sim` (replay the algorithm on a call tree; must reproduce *your* object's call set before you trust it for the target), `callsets --target-only` (which helpers stay calls in every target function). Callers sharing a body but showing different target patterns reveal which helper's cost differs. `#pragma dont_inline on/off` is a legitimate documented tool when the original evidently did it.

## Baselines, regressions and verification
- Before editing: record a baseline (`ninja baseline`, plus rich per-unit snapshots for units under investigation). At the end: rebuild affected units *and header consumers*, refresh the report explicitly, run a changes check, and compare section sizes (a negative `.bss` change may be real storage, a header's TU-local static, or a fuzzy-score change from splitting an anonymous range; find out which; never add padding to hide it).
- A successful ninja run does not always refresh the report after extracted objects change; refreshing reads existing objects and does not prove sources were rebuilt. Freshness checks report stale/uncertain evidence, not proof of correctness.
- A build with no header dependency tracking needs dependent objects deleted after header edits.
- Report which comparison mode you used (see pipeline reference).

## Conventions that pay off
- Original names wherever evidence exists; placeholders that encode the offset otherwise (`field_0x7c`, `FUN_10926680`, `Class_<vtable address>`); notes about evidence on their own comment lines (`// fabricated`, `// TODO:`, `// correct but X is incorrect`, `// rogue includes needed for matching sinit & bss`).
- Globals belong to a class as static members declared in its header and defined in its `.cpp`; do not use `extern` stand-ins (they hide ownership and produce wrong mangled names).
- Pointer vs reference and hidden return-slot parameters come from demangled signatures of any sibling-platform symbols (`Type const&` in the mangled name means the header must say so; a first param missing from the demangled signature is a hidden output buffer, so return by value).
- Match the project's era: pre-C++11 style for MSVC 6 (`no auto, range-for, lambdas, nullptr`), `clang-format` whole files before commit.
- Decompiled-library code (STL, CRT) is never published; game code that *uses* the library includes the real compiler header and uses its types.

## Parallel work
Give each agent explicit file ownership; serialize integration, config edits and builds that share a translation unit; hand off with changed files, evidence, verification commands/results, remaining mismatches and whether source/objects/reports describe the same revision. Do not touch/force-rebuild files while a human's objdiff is auto-recompiling in the background.

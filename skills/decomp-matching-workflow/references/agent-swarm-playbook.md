# Running many agents on a matching (or any bulk reverse-engineering) job

Source: Thief 3 decomp's `docs/agent-workflow.md`, `docs/matching.md`, `tools/agent/worker.md` (MIT), cross-checked with BW1's AGENTS.md "Parallel work", the `universal-modder` retro-decomp playbook, and LEGOLAND's CLAUDE.md. Numbers below are Thief 3's, measured on one MSVC 7.1 project; use them as priors, not laws.

## Roles
| Role | Does | Never does |
|---|---|---|
| **Lead** (strongest model) | prepares the queue, launches workers, sweeps results, reviews accepted code, owns shared files (headers, `symbols.txt`, `splits.txt`, `configure.py`, `src/`), runs naming passes and integration, parks out-of-scope items | take items from the queue itself; let workers touch shared files |
| **Worker** (cheaper model, tight protocol) | claims N items, writes `scratch/<ADDR>/vK.cpp`, runs the compile+diff tool, accepts or defers, returns one JSON line | edit shared files, run lead tools, write outside scratch, use git |
| **Gate** (a script, not a model) | compiles, diffs, applies the rulers, records `ACCEPTED`/deferral | accept anything on a model's say-so |

Model split that worked: small functions (<=31 bytes) to the cheapest capable model (Haiku 97% first-try; Sonnet 93% overall at ~20-30K tokens per match); 32-159 bytes to Sonnet (72-90% depending on band); >=160 bytes to the strongest model (Opus 67-83%, ~100-200K tokens per match). A second pass hands deferrals to the *other* model after the lead removes a blocker (Thief 3: 49 matches in 150 "hopeless" functions at another project).

## Worker protocol essentials (copy these ideas, not the text)
1. **One file, read once, ~2K tokens**, replacing skills and cheat sheets. The lead's prompt is one line of parameters: `Read tools/agent/worker.md and follow it exactly. ID=b05 FILTERS=--min-size 32 --max-size 79 --by-class N=6 COUNT=2 CAP=8`. Ids are never reused.
2. **Claim then context in one call**: `next.py claim --context --count K` prints the claimed items and per-item context packets (target asm, referenced symbols with names, similar accepted functions with their source, vtable slots, decompile, relevant idioms, earlier attempts).
3. **One attempt = one message**: Write `vK.cpp`, then `try && accept` chained, so a match is recorded in the same turn. Write source via the Write tool, not shell heredocs (guards that parse commands choke on `->`, `>>`, apostrophes).
4. **Env var per call** (`AGENT_ID=<ID>`): subagents share the lead's environment and do not keep variables between calls.
5. **Caps**: 5 attempts (tiny), 8 (main), 10 (big); the tool refuses after 3-4 consecutive attempts with no new best. Handled = accepted or deferred; keep claiming until N or `"empty": true`.
6. **Classify before each retry**; defer with a slug-prefixed blocker (`tiebreak:`, `inline:`, `layout:`, `vtable:`, `signature:`, `name-conflict:`, `library:`, `engine:`, `compiler-generated:`, `asm:`, `eh:`, `switch:`, `codegen:`). The lead counts slugs and unblocks in batches.
7. **Final message is only JSON**: `{"agent","matched":[...],"deferred":[{"addr","best","why"}],"needs":[<=3 x 25 words],"idioms":[<=3 x 25 words],"empty":bool}` so reports do not flood the lead's context.
8. **Plausible source only**: no register-named variables, no function-declared data, no `volatile` to keep stores, no invented classes, no inline asm. These all passed the byte gate once and were rejected in review.
9. **Defer instantly** on: hand-written-asm shapes, library code (STL/CRT/middleware), engine-vendor code you may not publish, compiler-generated shapes (adjustor thunks, deleting destructors, global initialisers, implicit ctors/dtors matched only with their emitting function).

## The gate and its rulers
A compiled candidate uses compiler-decorated names; the target uses `symbols.txt` names (`FUN_x`, `DAT_x`). Pairing by name fails for correct code when a callee is still a placeholder. Fixes: (a) *binding*: once a caller is accepted, the callee's decorated name is recorded and later definitions must use exactly that name or defer `name-conflict`; (b) a naming pass by the lead after each batch (old guess kept as an alias so earlier callers still match); (c) rulers for relocation targets and data values so a wrong constant never matches; (d) a check that every accepted function still matches once integrated into its real translation unit (MSVC inlines small same-TU functions defined *anywhere* in the file, so scratch files must declare callees, never define them).

## Queue design
- Order by difficulty score (instructions + 3/conditional branch + 2/call + 10/switch + 10/EH frame + 1/x87 op) when a disassembler is available, else size. Refit weights from attempt ledgers.
- Atomic claims: write a temp file then hard-link into place (fails if present); expiry (2 h) renewed by each attempt; takeover under a short lock; re-check the accepted/deferred records *after* taking the lock.
- Families (functions identical except for referenced symbols) are served one member at a time; once one is accepted, a "stamp" tool matches siblings mechanically. Thief 3 matched 68 wrappers this way.
- Exclusion list for out-of-scope items so no second pass serves them again.
- `scripts/claimq.py` in this skill is a minimal dependency-free version of claims, ledger and sweep.

## Cadence
Continuous swarm (8-16 workers, refill each freed slot at once) with a checkpoint every 16-20 finished workers: sweep (accept forgotten MATCHes, release stale claims, park out-of-scope, stamp families, print costs by band and deferrals by slug) → review `accepted/*.cpp` (grep for cheat patterns; read a sample) → naming pass → deleting-destructor/thunk passes → integration → library scan → report. Stop launching during re-split steps (they rewrite target objects the tool reads). Measured: 109 workers in three swarms; later 105 workers (343 + 141 + 68 matches in three bands).

## Cost levers
- A headless `claude -p` worker carried ~63K tokens of default system prompt per request (~2M input tokens per match) versus ~12.6K for a purpose-built subagent type with CLAUDE.md omitted. Use a restricted agent definition (tools: Read, Write, Edit, Glob, Grep, Bash; no CLAUDE.md load).
- The expensive tail is items that cannot match (inline-asm, undeclared class, library code); one worker burned 8M tokens on an asm function with experiments outside the tool. Forbid side experiments and exclude these shapes up front.
- Workers stop after ~100 tool calls following instructions less well (LEGOLAND); keep N small (4-6 for big, 20 for tiny).
- Success curve by attempt number (Thief 3): 77% first, then 65%, 37%, 39%, 23% of survivors; patience 3-4 saves tokens at the cost of ~0.2% matches.

## Human-in-the-loop rules that appear in every agent-friendly project
Ask before launching the game or deploying into the game folder; close the game after each test; the human commits and pushes unless told otherwise; keep raw decompiler output, disassembly, binaries and game data out of the repository; a clear evidence-level vocabulary; handoff docs (`docs/handoff.md`) listing current status and next steps so a fresh agent can resume; Conventional Commits.

## Also useful from other projects
- BW1: baseline snapshots before editing, decomp-regress/decomp-verify scripts, explicit file ownership per parallel agent, handoffs with changed files + evidence + verification results.
- jak-project AGENTS.md: disclose AI use in every message "(AI-assisted)"; never create issues or PRs unasked.
- universal-modder retro-decomp playbook (a public write-up of one N64 project): one function at a time with a build-and-verify script, attempts in their own files with a hard cap (~10), commit every match, shared `LEARNINGS.md`, rank candidates cheapest first, several worktrees in parallel, another model on the hard ones; budgets can reach billions of tokens.
- Verify AI-written matches deterministically (CRASHBANDICOOTXS/BattleTanx notes: "nothing is trusted on the AI's say-so"; every function is checked against the original ROM).

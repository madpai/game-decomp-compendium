# Legal posture and community etiquette

None of this is legal advice. It is the consensus practice seen across ~790 catalogued projects and the agent-oriented projects read in depth.

## What goes in a repository
- **Source only.** Your hand-written code, build scripts, symbol/split tables (addresses + names), progress reports, docs.
- **Never**: the game binary, disc/ROM images, extracted assets, raw decompiler output, bulk disassembly, license keys, DRM-removed binaries, leaked SDK/source code, or anything derived directly from them beyond short documenting snippets.
- The user supplies their own copy; builds verify by hash (`build.sha1`, sha256 in `reccmp-project.yml`).
- Many projects use CC0 for their source (89 of 304 in the GameDecompLibrary snapshot), MIT or similar for tooling; engines with an upstream licence (e.g. id Tech GPL-3.0) keep it. A repo with no licence file is not free to copy: paraphrase and cite instead.

## Leaks and "clean" projects
Some projects refuse contributions informed by leaked source or SDKs (and some therefore refuse AI help, because models may have seen leaks). Knowledge from betas/leaks may be fine to *describe* in your own words in some communities and unacceptable in others; check the target project's rules before contributing. Do not fetch or paste leaked material into any repository.

## AI policy: check before touching anything upstream
The catalog's `ai` field is a reading aid, not a ruling:
- `human-only`: the README forbids AI-generated contributions (one project also forbids agents indexing or modifying the repo). Do not ingest, clone or contribute; the clone helper refuses these.
- `no-ai-decomp`: AI may help with cleanup/naming/docs but not decompilation work.
- `disclose`: AI help welcome only if disclosed.
- `ai-ok`: the project itself uses or welcomes AI with verification (Thief 3, BW1, AVP2, LEGOLAND, jak-project...). Still read CONTRIBUTING.
- `mentions`/`unspecified`: unknown; read CONTRIBUTING.
Rules for agents: never open issues or PRs on the user's behalf unless asked; disclose AI assistance ("(AI-assisted)") where policy says so; never submit unreviewed machine output; prefer contributing tooling and documentation over matched functions to projects that are wary of AI.

## Modding and online games (universal-modder's hard rules, adopted here)
- Only games the user owns; single-player/offline, or servers the user hosts.
- Never inject into or debug an online client protected by anti-cheat (EasyAntiCheat, BattlEye, Vanguard, VAC on official servers, Ricochet, ACE, Javelin). Never write aimbots/ESP/speedhacks. Never bypass anti-cheat, DRM or ownership checks; if a loader needs a DRM-patched exe, stop and tell the user.
- Close protected games before RE sessions: debuggers and overlays can trip anti-cheat even if you do not touch the game.
- Back up saves/config before any modded launch; kill processes by exact PID; bind any bridge/debugger/MCP to 127.0.0.1 with a token.
- Do not publish retail offsets or decompiler-generated names baked into shipped mods; publish your code and converters, not game data.
- Takedowns happen even without assets (re3/reVC, H2M): keep projects non-commercial, ship tools/patches, credit sources.

## Credit
Cite the projects and docs you drew on (this hub's catalog gives URLs and licences). Keep each source's attribution in THIRD_PARTY_NOTICES when redistributing derived text.

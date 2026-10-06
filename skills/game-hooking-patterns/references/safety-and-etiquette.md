# Safety, legality and etiquette for runtime modding

Adapted from universal-modder's `safety.md` (MIT) and the hard rules of this hub. Not legal advice; read the game's EULA/mod policy when it matters.

## The bright line: online and anti-cheat
- Single-player/offline or servers you run. Injecting into an online client breaks its terms and gets accounts banned; doing it for advantage is cheating. Refuse aimbots, ESP, speed/teleport hacks, recoil scripts, packet manipulation for multiplayer games, whatever the framing.
- Kernel or user-mode anti-cheat (EasyAntiCheat, BattlEye, Vanguard, EA Javelin, Ricochet, ACE, nProtect, XIGNCODE, mhyprot) is a stop sign for code injection. Allowed: official modding surfaces (Workshop, creative/map editors, mod kits), official offline modes that ship without the anti-cheat.
- Never disable or bypass anti-cheat, spoof hardware ids, tamper with DRM (Denuvo, Steam stub) or ownership checks. If a loader needs the exe patched past DRM, stop.
- Tools next to a protected game (debuggers, Cheat Engine, injecting overlays) can trip its anti-cheat even if you do not touch it: close protected games before RE sessions.
- VAC bans modified clients on VAC-secured servers: test with `-insecure` on a local listen server.

## Ownership and redistribution
- Mod games the user owns, from their own install or dumps. Do not download ROMs/ISOs/game files.
- Do not publish game files, extracted assets, decompiled source, retail offsets or decompiler names baked into shipped code. Do publish your code and assets, patches/diffs, converters/installers that transform the user's files at install time.
- Credit loaders and libraries; disclose AI use honestly (some communities ban undisclosed AI projects).
- Takedowns happen even without assets; commercial use and leaked material raise risk sharply.

## The user's machine
Back up first (saves, profiles, config; a restore path written in the journal). Loaders/proxy DLLs sit in the game folder: tell the user what you added and how to remove it; prefer a separate copy or mod-manager profile. Registry/config edits: back up the key first. Input automation takes over the mouse/keyboard: check the user is idle and ask before long runs. Kill by exact PID (`pkill -f` can kill your own shell). Bind bridges/debuggers/MCP servers to `127.0.0.1` with a token (some RE tools default to `0.0.0.0`). Run loaders only from their official repositories (look-alike repos spread malware).

## When to stop and ask
Online components with anti-cheat are involved; the only route is bypassing a protection; a step would delete/overwrite saves or game files without backup; publishing (always the user's call).

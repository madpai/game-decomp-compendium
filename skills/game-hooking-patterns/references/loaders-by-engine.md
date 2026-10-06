# Loaders, logs and gotchas by engine

Condensed from universal-modder's engine playbooks (MIT; full text: `hub.py show playbook:<id>` or the upstream URLs). Always check the loader's current release page: versions move.

| Engine / family | Identify | Loader / tools | Log | Notes |
|---|---|---|---|---|
| Unity Mono | `UnityPlayer.dll`, `<G>_Data/Managed/Assembly-CSharp.dll` | BepInEx 5 (`winhttp.dll` doorstop) or MelonLoader (`version.dll`), Harmony; ILSpy/dnSpyEx; UnityExplorer | `BepInEx/LogOutput.log`, `Player.log` (`AppData/LocalLow/<co>/<product>`) | Proton: `WINEDLLOVERRIDES="winhttp=n,b"`; patch `DontDestroyOnLoad` state on scene load |
| Unity IL2CPP | `GameAssembly.dll` + `global-metadata.dat` | BepInEx 6/MelonLoader (generate interop); Cpp2IL/Il2CppDumper + Ghidra scripts | same | stripped methods may not exist; register injected MonoBehaviours |
| Unreal 4/5 | `<P>-Win64-Shipping.exe`, `Content/Paks`, IoStore `.utoc/.ucas` | UE4SS (Lua/C++; `dwmapi.dll`/`xinput1_3.dll`), Dumper-7, FModel (+AES key), UAssetGUI/UAssetAPI, `repak`/`retoc`, UEVR | `UE4SS.log` | `*_P.pak` outranks originals; paks cooked for the wrong UE version crash; EAC/BattlEye titles: no |
| Capcom RE Engine | `re_chunk_*.pak`, `natives/` | REFramework (`dinput8.dll`, Lua with managed type system), Fluffy Mod Manager, RE_RSZ | `reframework/` logs | cosmetic-only online |
| FromSoftware | `eldenring.exe`, BND/DCX | ModEngine2 / me3 (offline, EAC off), Smithbox, WitchyBND, DLL mods (fromsoftware-rs) | loader logs | never online; seamless co-op is separate |
| Rockstar RAGE | `GTA5.exe` | ScriptHookV (+DotNet) + ASI loader, OpenIV, CodeWalker | `ScriptHookV.log` | story mode only; launch with BattlEye off; ReShade must load via ASI loader |
| Bethesda (Gamebryo/Creation) | `Data/*.esm`, `*.bsa/*.ba2` | xEdit, Creation Kit, MO2, script extenders OBSE/FOSE/NVSE(xNVSE)/SKSE/F4SE/SFSE, Address Library, CommonLibSSE-NG, NifSkope, BSArch | `Documents/My Games/<G>/SKSE/` | game updates break extender plugins; script removal can corrupt saves; see `bethesda-gamebryo-re` |
| Source 1/2 | `gameinfo.txt`, `*_dir.vpk` / `gameinfo.gi` | VScript, SourceMod/Metamod (servers you run), Source SDK 2013, Crowbar, VPKEdit, VRF (Source 2 Viewer) | console | VAC: `-insecure`, never public servers while injected |
| .NET/XNA/FNA | managed exes | tModLoader, SMAPI, Harmony/MonoMod, ILSpy | `client.log` | tModLoader requires the free app in the Steam library: add it, do not patch the check |
| Java | jars | Fabric/Forge/NeoForge (Loom, Mojang mappings), ModTheSpire, Mixin, Vineflower/Recaf | `logs/latest.log` | Loom 1.18 needed Java 25 to run Gradle in one report |
| Godot | `.pck` | GDRE Tools | - | - |
| GameMaker / RPG Maker / Ren'Py / Paradox / id Tech / LÖVE / HTML5 | `data.win`; `js/plugins`; `.rpa`; plain-text mods; WAD/PK3; zip; `app.asar` | UndertaleModTool; plugin JS; unrpa/unrpyc; `.mod` descriptors; GZDoom; lovely+Steamodded; asar extract | various | distribute patches, not modified data files |
| Genie (AoE2 DE) | `.dat`, `.sld` | genieutils, AoE2ScenarioParser | - | the exe may hard-code tables the data seems to allow (civ picker) |
| Retro consoles | ROMs/ISOs the user dumped | decomps, recomps (N64Recomp, XenonRecomp, PS2Recomp), emulator Lua (BizHawk/mGBA/Dolphin Memory Engine/PCSX2 PINE), IPS/BPS/xdelta patches | emulator console | never download ROMs/ISOs; ship patches |

Search "<game> modding wiki" before reverse engineering: community tools usually exist.

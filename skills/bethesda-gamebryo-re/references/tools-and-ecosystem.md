# Bethesda tooling and ecosystem

Sources: universal-modder `bethesda.md` playbook (MIT), catalog entries (`hub.py search "bethesda"`), READMEs of esplugin/libloadorder/bsa-rs/rust-bsa-ba2-handler read in the corpus.

| Task | Tool | Notes |
|---|---|---|
| Inspect/edit plugins | xEdit family (TES4Edit for Oblivion, FNVEdit, SSEEdit, FO4Edit), scriptable in Pascal; `xelib` | dump plugins to text; conflict view (red = conflict) |
| Official editor | Construction Set (TES4) / Creation Kit | cells, navmesh, dialogue, quests; the CS wiki documents script functions and condition semantics |
| Plugin parsing in code | `esplugin` (Rust, GPL-3.0; Morrowind through Starfield) | designed for LOOT/libloadorder; do not copy code into non-GPL projects |
| Load order | LOOT, `libloadorder` (GPL-3.0; includes OpenMW and Oblivion) | mdbook explains load order concepts |
| Archives | `ba2` crate from bsa-rs (0BSD), `rust-bsa-ba2-handler` (MIT: pack/unpack/list/verify with GUI), BSArch, Archive2 (FO4+) | Oblivion BSA v103, zlib |
| Meshes | NifSkope; Blender + PyNifly | NIF versions differ per game |
| Textures | DDS BC1/BC3/BC7 tools | |
| Mod isolation | Mod Organizer 2 (virtual FS, profiles), Vortex, Amethyst (Linux) | get managers from official pages only |
| Script extenders | OBSE (Oblivion), FOSE, xNVSE (FNV), SKSE64, F4SE, SFSE; CommonLibSSE-NG/CommonLibF4; Address Library | plugins in `Data/<EXT>/Plugins/*.dll`; updates break plugins unless version-independent IDs are used |
| Papyrus | PapyrusCompiler (Skyrim+; Oblivion uses the older script language) | |
| Bridge pattern | thin extender plugin + localhost backend (AI-NPC mods; the chasm-bridge-fnv design) | see `game-hooking-patterns` |
| Engine reimplementation | OpenMW (Morrowind; patched by OpenOblivion) | OpenMW upstream is the donor for rendering, Lua API, UI |
| Reconstructed engine sources for orientation | FNV Xbox 360 decomp (CC0; human-only AI policy) | structure and naming only |

## Pitfalls
Game updates break extender plugins; removing scripted mods mid-save can corrupt saves (test on throwaway saves); DLC changes masters (know your ESM list); fake manager repos with zip releases spread malware; Oblivion's ESM data may contain trailing OR conditions and unused CTDA tail bytes (14 non-zero in Oblivion.esm), so parsers must not assume cleanliness.

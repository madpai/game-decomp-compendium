# Halo sources and tools

## In the compendium catalog (`hub.py search halo`)
| Entry | What | Policy / licence |
|---|---|---|
| punpckhdq/halo | Halo CE build 2342 Xbox decomp; ninja + Xbox SDK compiler; ~15% code | CC0-1.0 |
| halo-re/halo | another Halo CE decomp (list-sourced, not read in depth) | check README |
| ChimpsAtSea/Reach | Halo Reach (Xbox 360) decomp | GPL-3.0 |
| twist84/halo3_cache_release_recomp | Halo 3 cache/release recomp | README states no AI: not ingested |
| rehan-remade/universal-modder (field note) | Halo 3 MCC content port into Minecraft; Reclaimer pipeline | MIT |

## Community tooling named in the sources
- **Halo CE (PC) editing kit**: Guerilla (tag editor), Sapien (scenario/world editor), Tool (tag compiler/cache builder) [D]. Open-source alternatives and utilities by the community exist (e.g. Invader) [D, not read in depth].
- **Assembly** (cache editor; its `Plugins/Halo3MCC/*.xml` give tag field offsets for MCC Halo 3), **Reclaimer** (C# library; MCC/Xbox cache reading and geometry export), **pdb-decompiler** (turns PDB debug info into headers; used by the Halo CE decomp for types), **vgmstream** (decodes FSB5/Vorbis banks), ffmpeg.
- Official Halo 3 Mod Tools (H3EK) were not needed to read shipped `.map` files.

## Reading plan for a new Halo question
1. `hub.py prior-art "halo <topic>"`.
2. Locate the subsystem in the decomp module table (SKILL.md); read headers, then source.
3. Confirm numbers on real data from the user's install (tag fields) with an assertion over all tags of that group.
4. Implement with an oracle (compare to the original engine's behaviour or to extracted data); record evidence levels.

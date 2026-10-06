# Choosing an approach: questions, cost drivers, risks

## Ten questions
1. Does a decomp/recomp/port already exist? (`hub.py prior-art`) Reuse beats rebuild.
2. Which platforms must it run on, and does the donor/runtime exist there (Android, Switch, web)?
3. Is the goal preservation/fidelity or new features (mods, high resolution, new platform)? Fidelity favours decomp/recomp; features favour source ports.
4. How big is the code base and which compiler/arch? PPC/MIPS console games with known compilers are good matching targets; LTO builds and encrypted/packed binaries are not.
5. Are symbols/debug info available (beta builds, other-platform ports, PDBs of later games)? They change feasibility by years.
6. Is the engine data-driven with documented formats (Bethesda, Source, Unity) so a donor engine can load it, or code-driven (custom logic in executable)?
7. What is the oracle? If you cannot say how you will detect a wrong behaviour, you cannot scale the work (or use agents on it).
8. Who owns assets and how will users provide them? (installer, converter, on-device import)
9. What is the legal posture and community policy (AI bans, leak sensitivity, publisher history)?
10. What is the vertical slice that proves the approach in a week?

## Cost drivers
Per approach: matching decomp scales with function count and compiler fidelity (agents help: see `decomp-matching-workflow`); recomp scales with runtime/OS/GPU reimplementation; clean-room scales with behavioural surface (AI, physics, scripting); donor engines scale with the semantic distance between donor and target (Morrowind to Oblivion: scripting, dialogue, quests, creatures, magic, tree rendering all differ).

## Risks and mitigations
- Silent behavioural drift: assertions over whole data sets, rule-status tables, scripted probes.
- Hard-to-verify mobile issues: logging and tap tracing, device test early.
- Legal exposure: no assets/leaks, non-commercial, disclosure.
- Upstream drift of the donor: pinned revisions + receipts.
- Agent overreach: restrict write scope, require gate acceptance, review accepted code for cheats.

## Worked comparison: Oblivion-class RPG on Android
Donor engine (OpenMW) + translation layers wins: formats are documented (ESM/BSA/NIF), scripts compile from source stored in the data, dialogue/quest rules are data-driven, and the executable's RTTI + string pivots give targeted evidence for the rules the data does not state. A matching decomp of Oblivion.exe would cost far more than the behaviours it would clarify. Use RTTI/string recon to settle specific rules (topic list construction, quest script delay, lip-sync), then implement and test against real data.

## Worked comparison: small 2D Windows game (Delphi/VB/MSVC)
Source recovery or matching decomp is tractable (Space Rangers recovered Delphi source; several MSVC 5/6 decomps reach 90%+). Choose reccmp/objdiff workflow, pin the compiler, link library objects, and verify by relinking.

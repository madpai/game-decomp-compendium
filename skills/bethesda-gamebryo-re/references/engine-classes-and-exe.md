# Oblivion.exe: engine class map and where things live

Source: `re-binary-recon/scripts/rtti_scan.py` run on the Steam build of Oblivion.exe (PE timestamp 0x462392c7), plus `string_xrefs.py` pivots. Addresses are deliberately omitted (build-specific, exe-derived): regenerate them locally in 0.15 s. Class names and hierarchy are interoperability facts; the raw dump is not redistributed here.

## Totals
1,715 vtables, 1,481 classes with a primary vtable. Families: ~322 `Ni*` (Gamebryo scene graph, streams, properties, controllers), 107 `TES*` (forms and components), 85 `bhk*` + 51 `hk*` + 5 `Havok*` (Havok physics wrapper), 61 `BS*` (Bethesda additions), 15 `Magic*`, 7 `SpeedTree*`, ~38 `*Menu` UI classes, plus processes, projectiles and many template instantiations (`?$...`).

## Hierarchy spine (RTTI base lists)
- `TESForm` (55 virtual slots) with mix-in components (`BaseFormComponent`: `TESFullName`, `TESScriptableForm`, `TESIcon`, `TESModel`, `TESWeightForm`, `TESMemContextForm`, `TESChildCell`...). Records are forms: `TESQuest`, `TESTopic`, `TESTopicInfo`, `Script`, `TESObjectCELL`, `TESWorldSpace`, `TESRace`, `TESGlobal`, `SpellItem`/`MagicItem`, `TESNPC` (80 slots) -> `TESActorBase` -> `TESBoundAnimObject` -> `TESBoundObject` -> `TESObject` -> `TESForm`, `TESObjectDOOR`/`TESObjectCONT`/`TESSound` (72), `TESObjectTREE` (93; `TESBoundTreeObject`).
- References: `TESObjectREFR` (105 slots; bases `TESForm`, `TESMemContextForm`, `TESChildCell`) -> `MobileObject` (129) -> `Actor` (239; also `MagicCaster`, `MagicTarget`) -> `Character` (239) -> `PlayerCharacter` (239); `Creature` (239). Projectiles: `MagicProjectile` family 137 slots, `ArrowProjectile` 129.
- AI processes: `BaseProcess` (322) -> `LowProcess` (347) -> `MiddleLowProcess` (348) -> `MiddleHighProcess` (358) / `HighProcess` (358): the level-of-detail actor process hierarchy (higher = more simulation detail near the player).
- Scene graph: `NiRefObject` -> `NiObject` -> `NiObjectNET` -> `NiAVObject` (33) -> `NiNode` (39) -> `BSTreeNode` (57; SpeedTree trees), `SceneGraph` (39); `NiTriShape` via `NiTriBasedGeom`/`NiGeometry`. Streams: `NiFile` -> `BSFile` (16 slots).
- Shaders: `BSShader` -> `NiD3DDefaultShader` ...; `SpeedTreeLeafShader`, `SpeedTreeFrondShader`, `SpeedTreeBranchShader` (+ `...ShaderProperty`, `...ShaderPPLightingProperty`, `...ShaderLightingProperty`): the tree rendering path.
- Dialogue/quest: `TESQuest` (+`TESScriptableForm`), `TESTopic`, `TESTopicInfo`, `TopicInfoArray`, `DialogMenu`, `DialoguePackage`, `ExtraInfoGeneralTopic`, `ScriptEffect`.
- UI menus (a roadmap of screens a faithful port needs): `MainMenu`, `PauseMenu`, `HUDMainMenu`, `HUDInfoMenu`, `HUDSubtitleMenu`, `DialogMenu`, `InventoryMenu`, `ContainerMenu`, `MagicMenu`, `MagicPopupMenu`, `AlchemyMenu`, `EnchantmentMenu`, `EffectSettingMenu`, `LockPickMenu`, `NegotiateMenu` (barter), `PersuasionMenu`, `BookMenu`, `MapMenu`, `QuickKeysMenu`, `LevelUpMenu`, `ClassMenu`, `RaceSexMenu`, `LoadingMenu`, `LoadgameMenu`, `OptionsMenu`, `GameplayMenu`, `AudioMenu`, `VideoMenu`, `ControlsMenu`, `CreditsMenu`, `MessageMenu`, `QuantityMenu`, `TextEditMenu`, `BreathMenu`, `GenericMenu`; widgets: `Tile`, `TileMenu`, `TileRect`.

## Using the map
- Slot counts approximate interface size and virtual-hook surface; `Actor`-family 239 slots is where AI/combat/magic hooks live.
- Constructors store vtable addresses: xrefs to a vtable VA find constructors and factory sites.
- RTTI base lists let a tool classify any pointer (is it a `TESForm`? a `NiNode`?) without parsing code.
- Extender communities (OBSE and its Oblivion-specific data) hold struct layouts for these classes; verify against this build before trusting.

## Pivots already proven (strings)
- Script command names (`GetStage`, `SetStage`, ...) are referenced from the command table in data; each table record is 40 bytes.
- Voice path assembly: `Data\Sound\Voice`, `%s_%s_%08X_%u`, type strings `mp3`/`wav`/`lip` (keys `sFileTypeGame:Voice`, `sFileTypeSource:Voice`, `sFileTypeLip` in the same string block).
- Load/validation error formats embedded in the exe name many internal operations ("LoadGame ... variableID %d on '%s' (%08X) -- variable not found", "Linked door (%08X) in teleport data points to invalid object", "PlayGroup Error: Sequence '%s' not found"), each a pivot to the routine that implements it. `string_xrefs.py --grep` finds them.
- FaceGen texture/model settings keys (`bFaceGenTexturing:General`, `fRaceGeneticVariation`, race body texture model keys) sit next to emotion names (Surprise, Happy, Sad, Fear, Disgust, Anger, Neutral): the facial-expression channel for dialogue.

## Cross-reference
Fallout: New Vegas' Xbox 360 MemDebug decomp (`ieee802dot11ac/fnv`, human-only policy) reconstructs Gamebryo 2.2 and many `TES*` class headers (`TESCondition` with `IsTrue`, `ForceTrailingAnd`, `CheckValue`, comparison symbols; `TESForm`, `TESGlobal`...). Use for naming orientation and structure intuition only: its layouts are for a different game and platform.

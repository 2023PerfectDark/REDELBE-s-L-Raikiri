# Stage-selection captions

The optional `[Misc] slot_info_in_sss` hook observes the game's native UTF-8 texture setter, filtering the stage-select layout `d0805c2d`. The original REDELBE formatter hook compares `stage_%02d_%d`; LR's corresponding formatted calls reach the native setter at reference RVA `21c1330`. No absolute RVA is used at runtime.

`generate_stage_pattern.py` generates a masked complete-function signature; both baseline and 1.11 images match uniquely. Runtime lookup requires a unique exception-table function of the correct size and validates a complete 17-byte, relocation-free prologue. Failure skips only the stage caption hook. The setting off installs no texture hook.

The caption uses native pane `f121f112`, instance 0, text type 4, matching the original stage-caption routine at original DLL RVA `12331`. Texture calls are forwarded unchanged. Numeric preview IDs map to canonical stage resource codes. Alternate lighting/material suffixes are excluded. Sweat is `stage_13_1` → `S1301GYM`, as independently supplied by the user. Stage mods are not activated by this feature: named slots report Vanilla.

Tests cover Sweat, multilevel stages, suffix ambiguities, Random, unknown IDs, unrelated names and malformed names. Installed first test build SHA256 `e344a0d14f863d539d38b37ae944c5146d48623e21539bf8d1cd60ff955fe614`. In-game texture naming, caption lifetime, Random behavior and returning to character select still require the visual test.

User confirmed captions work in-game. At user request, Random and Unknown fallback captions now display Slot: Random Vanilla Stage/Modded Stage. Stage loading behavior is unchanged.

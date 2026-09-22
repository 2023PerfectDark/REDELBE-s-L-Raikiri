# Original REDELBE reference notes

Sources: user-provided original DOA6 readmes and changelog, archived in evidence/original_redelbe_docs. These document original behavior; they do not authorize or prove equivalent LR behavior.

- User confirmed the new LR settings build works on 2026-09-18. Alternative settings combinations remain untested visually.
- Original activation: F / Back / Select / Share in the appropriate costume or hair menu; LT/L2 traverses the opposite direction, at >50% trigger pressure. Preserve the user's already-confirmed LR direction mapping rather than silently changing it to match this readme.
- Costume/hair mod.ini uses [General] type, [Costume]/[Hair] slot, optional [Face], and work substitution. Original documentation warns that shared work resources can affect both players.
- Stage Layer2 supports KIDS and Field4 folders (0.9), stage captions, and random stage mods. These remain unported to LR.
- Special original stage work codes: BOSS, BOSSL, COLNIGHT, RRNIGHT, THROWA. They invoke original loader patches, not just ordinary resource substitution.
- [Stage] disable_npc=true supports specified arenas (expanded to Sweat in 3.0); bgm names use SRSXtool-extracted SE1_Common_BGM.srst filenames without extensions (2.9).
- Random music fullmix uses fullmix.ini (3.0).
- Regression cases for future ports: random-stage sky/lighting desynchronization (2.3), stage random selection synchronization (2.9), inactive Layer2 external .srst crash (2.61), repeat-battle selection persistence (0.6).
- No explicit rain, snow, or weather configuration instructions were found in these three documents or the supplied Optional Extras/Patches. Do not invent rain/snow INI keys or claim weather support from these references. Inspect an actual weather stage mod or relevant game resources before implementing it.

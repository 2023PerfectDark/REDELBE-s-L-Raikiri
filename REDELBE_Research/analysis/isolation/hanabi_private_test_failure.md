# Hanabi private texture test: failed in-game

User reports Hanabi outfit textures overwrite Kokoro while Kokoro face, eye and body textures overwrite Hanabi. The installed 16-ID test is NOT successful private isolation. Static overlay verification established serialization and vanilla payload integrity only.

## Confirmed design defects

- prepare_hanabi_private_test.py replaces existing Kokoro texture-object references in MaterialEditor. It does not create independent material objects or model definitions for Hanabi. Vanilla Kokoro and Hanabi therefore still address the same object identities.
- layer2_runtime.h, l2::select, searches both active fighters for a requested resource. The requesting fighter's Vanilla selection does not prevent the other fighter's mod replacement from being returned. File routing also cannot separate a resource already shared in the game's object cache.
- Main loader.log shows P2 requesting KOK_COS_001 (afcd1bdf) with choice=0. Do not claim this alone proves what P1 displayed; user confirmation of the simultaneous-fighter case is pending.
- The outfit and separate hair/head package intentionally share the new texture IDs, which is compatibility, not independent per-mod isolation.

## Read-only investigation this turn

- audit_hanabi_material_graph.py: the supplied face MTL/KTID words do not directly match MaterialEditor OIDs or property values. Blind replacement of these words is not justified.
- audit_hanabi_model_chain.py: CharacterEditor model roots identified as 42001fe7 (face), 524a6ccf, dce47e42. Traversal of matching object IDs reaches 103/104 objects but does not reach texture resource properties. This exploratory traversal is not a validated schema and must not be used for automatic cloning.
- Reports: hanabi_material_graph.json, hanabi_model_chain.json, hanabi_model_closure.json.

## Required next implementation

Resolve the model-to-material binding by actual schema/native lookup; clone Hanabi's material objects and their texture references instead of editing Kokoro's originals. Allocate separate model/selection identities as needed to avoid shared caches, and route only the modded fighter to those identities. Preserve original Kokoro material records and test Hanabi and Vanilla Kokoro simultaneously in both player orders, plus cycling and separate hair/head choices.

No new runtime build or live asset changes were installed during this investigation. Existing rollback is main/REDELBE_LR/rollback/hanabi_private_20260921_062432. Do not ship the failed test as a completed feature.

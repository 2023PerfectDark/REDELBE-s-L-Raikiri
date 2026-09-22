# Automatic private Layer2 assets — installed, regression pending

## Current status — 2026-09-21 13:21 (supersedes historical notes below)

User confirmed player-specific routing: Hanabi keeps her appearance in a fight while Vanilla Kokoro is unchanged. Automatic preparation is now integrated in bridge version 7, built and installed in the main game. Native routing supports numbered private aliases and independent hair/head selection overrides.

Installed generation: sets/20260921_132001_1c4d04db. All seven character mods report isolated, plus preserved RRPreview: 8 verified mods, 29 mod assets, 1158 vanilla/dependency assets. Second installed Sync returns unchanged. Sixteen Python tests plus native private routing tests pass. Build succeeds with pre-existing warnings.

Rollback checkpoint: REDELBE_LR/rollback/automatic_private_20260921_131942. Includes previous DLL, Sync executable, active pointer/state and original Hanabi package/project markers. Portable legacy recipe embedded in both Hanabi package/project markers. Game restarted for regression; still need user verification of newly automatically prepared Hanabi and other mods. Do not treat preparation verification as visual verification of every mod.

User instructions: README Automatic Layer2 Isolation.md. Unsupported private preparation keeps classic activation with a report; unknown legacy resources still require porting. No release ZIP updated.

## Historical notes

### Hair-color prompt regression fixed — 2026-09-21 13:32

User reported visual isolation okay but Wardrobe hair-color prompt absent. Loader logged zero hair catalog entries. Automatic generations omitted the old palette catalog and assets (even manual private_grp generation lacked them). Added permanent REDELBE_LR/HairColorSupport, migrated from sets/hair_palette16_roster_01 using hard links for large immutable palettes, native paletteRoot prefers permanent location, Sync v8 reapplies only hair resource routing/baselines before private cloning. Saved HairColors.prototype.ini untouched. New verified generation sets/20260921_133137_0d2543bd: 8 mods, 29 assets, 1246 baseline/dependencies. Rollback hair_support_20260921_133133. Restarted; visual prompt verification pending. No claim that custom colors now recolor every isolated mod-specific hair texture; this fixes missing Wardrobe UI/catalog and vanilla palette routing.

User requests the Hanabi isolation method for all future Kashira and REDELBE LR character Layer2 imports. Do not declare this complete: sync and battle routing are not integrated yet.

Confirmed by user: v8 private package renders separate Hanabi and Vanilla Kokoro bodies in Character Select. User then tested a match: Hanabi becomes Vanilla Kokoro. Existing loadHook still passes original model slots to loadOriginal. This is the current blocker before automatic isolation can be enabled safely.

Preparation added:
- tools/private_model_preparation.py: reusable clone_model for arbitrary native costume/face/hair chains, texture binding overrides, optional legacy MPR reconstruction, independent support files, and mesh binding bounds checks. Not connected to sync yet; needs real package regression tests.
- tools/model_slot_registry.py: explicit source mappings and collision-checked private name allocator; tested 500 allocations for one slot plus preserved registry metadata (4 tests pass).
- lr_resources.extract equal-size compression correction remains in place.

Native: removed the uninstalled speculative owner+168 preservation code, disproved by same-P1 Vanilla comparison. Added diagnostic logging only to existing loadHook: object/context/extra/caller and 32 readable context bytes. Build succeeded with prior warnings. Installed trace DLL only, verified v8 package retained. Rollback: main REDELBE_LR/rollback/private_battle_trace_20260921_125353. Game restarted. Next: user enters P1 Hanabi/P2 Vanilla Kokoro offline match to capture ownership evidence. Do not infer ownership solely from costume or load order in mirror matches.

Remaining: verify player-specific battle routing; generation-wide private clones and registration; import both Kashira and loose Layer2 paths; preserve noncharacter mods and unsupported classic activation; portable legacy binding dependencies; atomic sync reports/cache invalidation; multi-mod/hair/costume composition tests; install rebuilt Sync after integration. No automatic fallback should silently disable a mod. Do not claim legacy DOA6 mods are universally auto-ported.

## Battle routing candidate installed — 2026-09-21 12:58
Diagnostic showed both fighters share the same load context and extra=0; hashes/load order are insufficient. Read-only caller tracing found native outer constructor0x39e1870(result,context,fighterIndex,character,slot28,extra). Its r8 byte selects existing fighter via3a5c4b0; caller397cbcf passes sil while r9=character. Generated full-function297-byte masked pattern (call and RIP displacements masked), unique runtime-function resolution and16-byte whole-instruction trampoline. Thread-local scoped fighter index is consumed only inside existing loadHook. Copy28-byte appearance struct locally and replace only costume/face/hair for selected private mod, preserving caller and gameplay identity. Unknown/non-P1/P2 contexts remain unchanged. Random activation still runs before private selection. Needs in-game verification, especially rematch/reversed sides.
Installed DLL candidate; active v8 package unchanged. Rollback private_battle_route_20260921_125828. User asked to test P1 Hanabi/P2 Vanilla Kokoro. Build passes with prior warnings. New general clone_model successfully cloned all three current Hanabi chains twice with independent setting IDs (74 new resources) and original-record preservation. Automatic sync still NOT connected/enabled; continue after battle result.

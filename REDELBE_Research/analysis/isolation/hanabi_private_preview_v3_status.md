# Hanabi private preview v3 — installed, visual verification pending

## Requirement

Keep Hanabi active. Prefer independent/unused assets; shared fallback is allowed by user if necessary. Vanilla Kokoro and the opponent should retain their appearance wherever isolation succeeds. Background assets were suggested as donor candidates, but occupancy is not proven.

## Discovery

Kashira.Core/Doa6/Doa6SingletonSet.cs and MaterialChainFactory.cs describe the missing chains. Base KTID references resolve into CharacterEditor as well as MaterialEditor. Costume material overrides are rooted in CE1Common CharacterSetting/CE1MotorCharacter. The previous MaterialEditor-only patch did not isolate these chains.

## Implemented

- isolated_material_chain.py: independent texture objects, KTIDs, texture-bind objects and material objects. Original DOK records remain byte-identical. Source/resource collisions are rejected.
- Material preparation: 28 material clones, 257 texture objects, all 16 Hanabi replacement textures matched.
- build_hanabi_private_preview.py: adds KOK_COS_901 / KOK_FACE_901 / KOK_HAIR_901 model-resolver entries with cloned setting/motor/model definitions and independent model/support files. This uses newly allocated entries rather than overwriting a background donor whose occupancy is unknown.
- All previous original-file redirects were removed from this generation's full Hanabi mod. Its new files are independently addressed and are only needed when the private model is requested.
- Native [PrivateModel] opt-in routing changes only model request arguments for the selected mod/player; original gameplay character, UI selections and other player arguments stay unchanged. Opponent/donor conflict falls back to ordinary routing, never disables the mod.

## Validation

- Three Python clone tests pass, including two independent replacements, preserved original records and collision rejection.
- Native private-route test passes: independent player arrays, unchanged unrelated hair, disabled default, donor conflict fallback.
- Combined DLL builds with pre-existing birthday_display, preview_music, mouse_menu and export warnings.
- Generated overlay verifies: 8 mods, 73 mod assets, 222 fallback assets. 119 new independently addressed files.
- Loader initialized after normal restart; visual outcome is not confirmed.

## Installed state

Main game active package: REDELBE_LR/sets/private_preview_20260921_070320

Rollback: REDELBE_LR/rollback/private_preview_20260921_070320 (previous dinput8.dll, active_package.txt, loader.log).

Workspace package: packages/hanabi_private_preview_v3

This is a disposable character-select preview generation. Sync can replace it; it has not been integrated into Kashira sync/export. Battle load routing is not complete and must not be claimed as tested. User was asked to test only Character Select with P1 Hanabi and P2 Vanilla Kokoro.

The existing inspect_preview_objects.py uses old offsets and produced invalid RTTI/model-container output, followed by a console encoding error. Do not use that dump as validated runtime model evidence.

## v4 correction and current state

User reported startup crashes with v3. Restored its checkpoint immediately. Offline inspection found the registry's names/settings arrays extended to 1703 while CharacterKeyHashArray and two companion arrays remained 1700. Added model_slot_registry.py and two passing tests that validate all four parallel arrays, hashes, unique names and matching lengths. New registry rows retain source companion metadata, change name/hash/setting, and preserve alphabetical order.

Installed v4: REDELBE_LR/sets/private_preview_20260921_070649. Rollback: REDELBE_LR/rollback/private_preview_20260921_070649. Main PID 3764 reached update notices and stayed running after restart. User has been asked to test P1 Hanabi versus P2 Vanilla Kokoro in Character Select; result pending. The native source and DLL are the same opt-in private-route build; only prepared registry/package was corrected.

Potential next check if face textures are misaligned: original Hanabi KOK_FACE_001.ktid contains 34 bindings whereas native LR has 35 (extra index 16). Current cloner uses native binding data. Compare source-mod binding order before claiming all face textures work. Do not silently change unrelated native entries.

## Current status: 2026-09-21 07:42 local (supersedes rollback below)

Active: sets/private_preview_20260921_074246, package hanabi_private_preview_v6. Rollback of previous face-working build: rollback/private_preview_20260921_074246.

Native companion fallback and private hairstyle identity preservation fixed the two activation crashes. Companion lookup at RVA 0x37672c0 falls back to source model only when private lookup returns zero. The request callsite at request+0xb0 preserves private hair identities instead of canonicalizing them to zero. No null-check suppression was used.

User confirmed eyes/hair separate in v4-derived candidate, then face textures working in v5. Body remained missing. v5 preserves the custom Hanabi face KTID's 34 entries instead of native LR's 35.

v6 restores original DOA6 body KTID (22 entries rather than LR's 21) only in the private body. Missing legacy texture context is imported under a new private object ID; its resource was verified present. Body mesh texture index 21/category 47 was previously out of range. Audit now finds no invalid texture indices in body/face/hair. Four cloner tests and package verification pass (8 mods, 73 mod assets, 222 fallback assets). Installed and restarted normally; awaiting user visual result.

Remaining: body visual verification; possible native MBE/KTS compatibility if base table is insufficient; reliable battle ownership routing; sync/project integration. Preview routing only, do not claim complete isolation. Sync can overwrite this disposable test package.

## Historical v4 activation failure; restored baseline

User reports activation crash. Restored dinput8.dll and active_package.txt from private_preview_20260921_070649. Active package is again sets/20260921_062436_31464d16 (the pre-preview, non-isolated Hanabi test). Reopened main game, PID 34732 at last check. No v3/v4 preview remains active.

Crash dump: C:/Users/Owner/AppData/Local/CrashDumps/DOA6LR.exe.3764.dmp.
Saved log in rollback/private_preview_20260921_070649/failed_activation_loader.log.

Crash is access violation at game RVA 0x2d57996: cmp qword ptr [rcx+0x68],0, with RCX=0. Live disassembly of restored same-version code shows caller RVA 0x22cf211 takes the pointer from request object +0x58 and calls 0x2d57990 with EDX=0x1b58 (7000). Other request components +0x60/+0x68 were populated. This is a missing request component, plausibly motion-related; exact type is not verified. It is not evidence that skipping the null check would produce a valid model.

The synthetic slots have not been proven complete runtime model identities. Do not reinstall v4 unchanged. Next work should resolve the +0x58 component/associated lookup, or use a known complete donor identity with proper ownership/restoration. Background-model names alone do not establish animation compatibility or that a donor is unloaded. Do not claim full isolation or match support.

Read-only reports: private_preview_crash.json, private_lookup_code.json. inspect_private_preview_crash.py must use loaded dump instruction bytes (on-disk game code is protected). read_private_lookup_code.py obtained surrounding caller disassembly from the restored live process with existing local capstone/pefile dependencies.

## v7 material-bundle test — 2026-09-21 07:46 local

User confirmed v6 body still missing; face remained textured. v7 is now installed at sets/private_preview_20260921_074625; rollback/private_preview_20260921_074625 saves v6.

Kashira CostumeAuthorInstaller documents body base KTID as inert when MPR material bundles are selected. Added private_mesh_materials.py to derive KTS categories and ordered MPR texture references from each custom body mesh material using the already-private base texture objects. Body MI is now filled with these three materials across its eight variations; MRNH uses the same private MBEs. Native original objects remain byte-identical via serializer checks. Face/hair cloning remains unchanged. Six additional resources (three KTS, three KTID). Package integrity passes, plus audit validates all 24 body variation entries against mesh categories and private texture references. Awaiting user visual result; do not claim body fixed yet.

## v7 failed; live model-state investigation

User reports v7 body still missing. No new installation yet. Main game PID32160, v7 package still active. read_private_model_state.py used matching DLL link map to read known l2::requests at DLL RVA0xc6100. Snapshot live_private_model_state.json confirms body/face/hair request+60 and +68 are populated. Owner P1 0x7ff62d342f08; P2 0x7ff62d3431e0 (valid ONLY for PID32160). P1 body render+8c=8 vs P2=9, model+16=0 vs1 and +48=0 vs1. P1 owner+168=0, P2=1. Native request resets +168=(player==1); this may be render participation, not necessarily primary visibility. Need compare same P1 in Vanilla before concluding.

Pending async question asks user to cycle P1 to Vanilla and reply ready. Do NOT install while waiting for this state. A candidate preserving owner+168 during forceReload of a private model is prepared in layer2_runtime.h and compiles, but not installed or verified. Build/map now differ from installed DLL; the read script intentionally rejects mismatched build SHA. Previous known RVA0xc6100 came from verified matching old map. For next read use established snapshot owner only with verified unchanged PID/module, or recover previous matching map. Do not remove hash guard casually.

Saved disassembly files: function_22ca6e0.asm, function_22cbe80.asm, function_22cf180.asm, preview_update.asm, preview_visibility_writes.asm, visibility_apply.asm, visibility_set.asm, model_visibility_setters.asm. Captured executable analysis/lr_updated.bin is baseline; protected installed EXE cannot substitute. 22cf0d0 drives render bit0 from owner+168 indirectly; 22c3c70 sets render+8c bit0. Need establish whether shadow/reflection vs visibility. Body fully loaded alone does not prove shaders correct.

## Follow-up: body still missing, 09:33 local
Confirmed visually through computer-use screenshot: P1 Hanabi face/eyes/hair visible, body invisible; KOK_COS_001 selected. Automatic F keypresses did not register in loader log (do not infer Vanilla comparison occurred). Asked user once to cycle P1 to Vanilla for same-owner baseline; answer pending. Main PID32160 remains unchanged, installed v7 unchanged. No speculative DLL installed.
read_private_model_state.py now supports archived RVA0xc6100 only for exact installed SHA256 d7a01f433c1842cd7aeefe0134d3ae8db5cebfc1e357c83441217933dcc24449; other binaries still require matching build/map. Added labeled snapshots and PID/hash provenance. Fresh read saved hanabi_body_missing_baseline.json; all body components still populated. The pending owner+168 preservation candidate is NOT verified and must not be presented as a fix.

## v8 body GRP extraction correction — 2026-09-21
User confirms P1 Vanilla body returns. Captured vanilla_body_visible_baseline.json using same PID/owner. Owner+168 and render+8c unchanged between Vanilla and Hanabi, disproving previous visibility-byte theory. Model+48 differs (Vanilla1, private0); exact semantics not yet fully established.
Concrete data defect found: source body GRP0x8f7e49ec is compressed with flags0x400000 and both encoded/decoded sizes32. lr_resources.extract incorrectly returned compressed payload whenever sizes matched. Cloner wrapped it as raw private GRP0x0fa90015. Fixed equal-size shortcut to respect compression flag. Rebuilt v8; GRP decoded bytes now 1f225730000000000c00000000000000000000000c0000000000000000000000. Mocked compressed-equal-size/raw-equal-size extraction checks pass, plus rebuilt GRP matches decoded source. Package verifier passes 8mods/73assets/228vanilla assets.
Installed PACKAGE ONLY at sets/private_grp_20260921_124447; checkpoint rollback/private_grp_20260921_124447. Existing installed DLL retained (no speculative owner+168 patch). Normal close/restart succeeded. User visual test pending. Face/hair chains preserved. Not yet integrated with sync, battle routing remains incomplete. Installer script still points at v7 and speculative build DLL: do not run blindly.

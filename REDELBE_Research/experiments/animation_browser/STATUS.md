## Latest: F8 confirmation / camera request

Main DLL b2ed533dd08e7aa266826208c9465e7bea84587894e70c8d9c3487f600de39ac installed. F8 opens Yes/No confirmation in Wardrobe; defaults No. No/Back/Esc cancel; Yes opens list. Mouse, keyboard, controller handlers implemented. User confirmed Yes/No confirmation works. Camera controls captured from photo mode; details in CAMERA_PLAN.md. Training entry, fighter targeting, dedicated cameras and fallback/free camera remain NOT implemented. Do not claim these working. No new public release.

# Current status — 2026-09-21 browser preview

This section supersedes the historical notes below. Full browser with native cameras and clean public alpha release are NOT complete.

Installed DLL SHA256: 754e33b6613534871efcc5429fb2459ba01b96b73defc9576f174faa5c35e12e.
Rollback: main REDELBE_LR/rollback/animation_browser_controls_20260921/dinput8.dll.
INI [AnimationBrowser] enabled=true controls the browser; default is false. Diagnostic marker moved to rollback, so evaluator logging is disabled. F8 opens the owned nonactivating panel only in Wardrobe; closing/stopping/leaving Wardrobe disables substitution. Mouse controls and keyboard/controller navigation are implemented. New controller controls still need live validation. Corrected polling to refresh Wardrobe context before consuming controller input, avoiding TTL expiry and input leakage. Latest process 17440 reached startup with both browser catalog and evaluator pattern resolved.

Verified visually on previous build: both KAS07020_WIN and KAS07120_WIN play; Pause freezes body; switching clips resumes; Stop restores native Wardrobe pose immediately. Some clip root motion moves Kasumi below the Wardrobe frame (the Brad Wong visible behind is the static room background, not a changed character). Native animation cameras/facial sync remain unimplemented. Do not claim these motions are unused.

Catalog: 11,221 supported 0400 body clips extracted locally, errors=0. Standalone Prepare Animation Library.exe built and tested against main game into a separate workspace output: 11,221 clips, zero errors. It auto-finds game ancestors or accepts --game; no personal path required. Generated animation assets must not be packaged. Executable lives in packages/AnimationBrowser_Preview/Tools; this is a component staging folder, not the public release.

Next: test new controls, investigate camera evaluator + native camera format, then finish release allowlist/schema/docs. Current game restarted successfully and reached main-menu developer notice; dismiss with right-click without saving preference. No game archives or mod packages changed.

--- Historical notes ---


## Current update: native evaluator and opt-in playback proof (2026-09-21)

This section supersedes the older progress notes below. Public browser and release are NOT complete.

The live native evaluator at RVA 02dd7ad0 is now located with a unique pattern and captures real animation calls (caller 0300b234). The original VM wrappers captured no calls and must not be used as the normal playback path. The evaluator trace records up to 128 motion/skeleton pairs, 4096 records, once per pair every two seconds. No game resource pointers are retained for playback.

A live compact payload matched HON07000_CHRSEL.g1a (ff648f6a) by FPS, frames, bone count and full bone table. G1A 0400 has a 32-byte file header and retains its original bone-table encoding in the native compact representation. Native compact header: FPS +0, frames +4, bone count +8, version flag +12, bone table pointer +24, keyframe pointer +32, packed-vector pointer +40. Packed vectors are aligned. Native motion interface 4257c28 is a 32-byte object; data after that in old snapshots belongs to other objects, not extra fields. Constructor 2dc9900 and attachment 2e09110 confirmed this layout.

Added match_live_animation.py (read-only comparison), improved inspect_animation_evaluator.py, and animation_preview_test.h. The latter owns a validated 0400 clip and compact payload, copies a live native motion interface only for the duration of its original evaluator call, and refuses different bone IDs/counts. F8 arms it only in a freshly observed Wardrobe context; leaving Wardrobe disables it. This is an experimental body-only proof, not a finished browser, and has not yet been visually verified. Selected test clip KAS07120_WIN.g1a (0143fbdc) is extracted locally, not for redistribution.

Installed test DLL and clip in main game. Rollback: REDELBE_LR/rollback/animation_playback_20260921/dinput8.dll. Trace marker animation_evaluator_trace.enabled remains present. Current startup log confirms clip validation and native evaluator resolution. Next: navigate Wardrobe/Kasumi and explicitly test F8; verify animation, stop/restoration and no crash. Camera/UI/catalog selection/release still pending. Remove test clip and marker from public builds; do not ship game animation assets.# In-game animation browser research

## Resumed 2026-09-21

### Native trace installed 13:49

Update after second done: action_victory_trace.log again has ONLY three resolution messages, zero wrapper invocations. These VM wrappers do not serve this normal victory path; do not request more replay tests of them. Read-only battle_objects.json PID10884 base7ff6a72b0000 captured graph from latest battle load owner20543b692d0. Owner+10 resource descriptor(vtable42511d0), +18 native model(vtable426f7a0); model+150 pose container205b74030b0. motion_state_samples.json shows changing skeleton buffers at container+20/+28/+30; these are NOT proven playback control fields. Resource handle at container+40 points205b7402910; descriptor hash6537e681 is model resource, not animation. Generic RTTI heuristic yielded garbage names because no validated COL signature; ignore type strings unless valid. Next research should inspect native model animation dispatch/character action state, not change pose buffer values or guess replay methods. Diagnostic marker disabled for next launch; running hooks are pass-through only. Browser/release still incomplete. User told no further repeated match is needed currently.

Update13:54: user completed Kasumi win. Captured victory_trace.log contains only resolution messages, ZERO model/camera wrapper calls. Do not claim captured playback. Added third pass-through VM wrapper kids::placeable::model::ApplyActionWithCameraToEnd at33196f0, identified registration8c651d; .pdata first fragment280bytes. Pattern+20byte whole-instruction prologue validated by build. Trace cap raised1200 perkind, throttled500ms. Installed and restarted rollback animation_action_trace_20260921_135403. Need replay capture; if again no calls, stop using VM wrappers and inspect actual action-state/native playback dispatch. No browser UI or public release produced yet.

Read-only live scan PID23284 found 34 resource hash matches; 8.25GB scanned within45s, mostly name/index tables. No active playback ownership proven. Static registration analysis found kids::placeable::model::ApplyMotion VM wrapper at331c950 (254byte runtime function fragment), camera::ApplyMotion at331c770 (474bytes); registration constructors3311e50/3311dd0. Function-specific masked patterns generated and both unique at runtime. Added optional animation_trace.enabled-gated pass-through hooks, whole-instruction non-RIP prologues20/21bytes, logging128 readable contextbytes at most twice/second and120records perkind. No substitution/replay implemented. Build succeeds. Installed with rollback REDELBE_LR/rollback/animation_trace_20260921_134900; PID64996 started and both hooks resolved. User asked to finish another Kasumi win and reply done to capture calls. Remove diagnostic marker for release; trace is not browser functionality. native_playback.asm holds static wrapper disassembly. Trace cap may require rearming in later build if exhausted before victory.

Hair-color input fix user-confirmed. User requested finishing this browser, then preparing the public alpha. No browser hooks installed yet. Current game build remains hair_input_20260921_133601 with verified automatic isolation and restored palette.

Added tools/animation_catalog.py: explicit game path and optional name-map path, reads native RNKs where available, falls back to supplied map, inventories unidentified animation resource types without claiming unused/safe playback. Current game RNK payloads are absent; user's supplied Kashira Name2Hash CSV gives 12,510 named plus 5,701 type-based unknown entries (18,211 total candidates). Output native_catalog.json. No full PC path required by tool itself.

Static Kasumi animation resource hashes have no literal matches in mapped executable. CharacterEditor, CharacterEditor1Common and ActionController DB scans found no direct resource links. Do not infer native player functions from menu animation functions. tools/inspect_victory_memory.py prepared as read-only bounded live scan; not run yet. Pending asynchronous request: finish offline match with Kasumi winning, leave victory/results open, reply ready. Need capture before implementing playback and camera synchronization.

Public release packaging remains pending browser implementation/testing. Existing prepare_clean_release.py targets old RC4 and must be updated to latest feature/assets and portable configuration; do not run as-is or claim release ready.

User selected Kasumi as first DOA5LR victory-port candidate, then requested an
in-DOA6LR browser to inspect existing animations with their cameras first.

## Verified locally

- `catalog.py` joins the current LR root/system indexes with Kashira's name map.
- 12,510 named animation index records; this is not a count of every animation
  in the game, because unnamed resources are not included.
- Ten Kasumi victory resources extracted read-only and checked: two bodies,
  two cameras, six facial clips. No extracted game payloads saved by this tool.
- Bodies: KAS07020_WIN (0xa768919b), KAS07120_WIN (0x0143fbdc).
- Cameras: KAS_CAMERA_7020_WIN (0x16df3ea8),
  KAS_CAMERA_7120_WIN (0x9d64f947).
- Bodies/faces use `_A2G0400`; cameras use `_A1G2400`. Do not decode the camera
  with the body header layout. Camera associations are name matches only.
- No assertion that either pose is unused or missing from normal play.

## Not implemented

In-game browser UI, native playback/replay, camera synchronization, unknown
animation discovery, usage classification, and DOA5 conversion.
No loader or game files were modified in this investigation.

## Next step

User was asked to finish offline Versus with Kasumi winning and leave results
open. Inspect native victory playback/resource links before installing hooks.
Existing animationPlaying/animationReset loader symbols are UI-layout animation
APIs, not verified character animation APIs.

DOA5 research: chara_rtm.lnk uses CHRT, rtm_common.lnk RTCM; table appears to
begin at 0x20 with 32-byte records (offset, size, size, flags), but needs strict
validation before extraction. Catalogs are LFMO with obfuscated resource names.
eternity_common/DOA6/G1aFile.cpp ImportFromCsv is incomplete: only Hips mapping
is enabled; other mappings are commented out. It is not a ready-made converter.


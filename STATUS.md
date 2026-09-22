# REDELBE / Last Round status — 2026-09-16

## Portable pattern-based loader work

See REDELBE_Research/PORTABLE_RELEASE.md. Runtime patterns pass original and Ver. 1.11;
main updated game has the test build, backup remains on the user-confirmed working fix.
Packaging/installation/removal and native Kashira preparation pass. The two-DLL
prototype exited early; the final combined dinput8.dll fixes standalone startup.
User confirmed Ver. 1.11 menus and Minato Vanilla/mod cycling with both the legacy
bootstrap and the standalone build. RC2 is ready for wider testing, not a guarantee
of all future updates. Other-PC and Ver. 1.11 randomization tests remain outstanding.

User confirmed the prior shared model-scale correction fixed both Tina and Hanabi:
both display correctly and cycle back to Vanilla without crashing.

## Shared Tina/Hanabi model-scale correction installed — pending game test

Native scale consumer 22cc812 checks costume ID before calling the model-default
initializer. This outer check skipped the earlier source-identity fix entirely.
cache0 now returns false only at this verified call site (return 22cc817), allowing
the existing initializer hook to check model identity and rebuild via native code.
The consumer's +169 flag still gates processing to each newly loaded model.
No vector bounds checks disabled. Build, Layer2 state tests and 16 KB DLL-thread test passed.
Installed ASI SHA256: a5fb7a11fbe3439fe4de5fadbff5164b6191178645cdb16b20d0121178fe3cb5.
Backup: REDELBE_Research/backups/model_scale_before_20260916_213337.
Both Tina TIN_COS_105 Patriot Bikini and Kokoro KOK_COS_001 Hanabi need in-game retest.

## Hanabi Kashira project installed

IN-GAME TEST FAILED: activating Hanabi crashes. Dump DOA6LR.exe.34044.dmp
reaches the same native invalid-vector-subscript call site as Tina (22cc97b).
See REDELBE_Research/analysis/hanabi_crash_20260916.md. No fix verified.

Installed Hanabi into the authorized LR backup as
KashiraProjects/REDELBE_LR_Hanabi/project.ktproj, with its built package in _Kashira/Mods.
Slot KOK_COS_001 with KOK_FACE_001 / KOK_HAIR_001; Vanilla by default, normal Layer2 cycling.
Updated sync helper registers nine restored resources and patches eight exact material/character
references. All eight referenced Vanilla fallbacks match current LR bytes. Actual Kashira Editor
build and resource verification passed; full installed sync verified 33 mods, 730 mod assets,
and 306 Vanilla assets (sets/20260916_212238_6e377b2f).
Appearance and voice remain untested in-game. Tifa is not installed. ASI unchanged.
Backup checkpoint: REDELBE_Research/backups/hanabi_before_20260916_212233.
This installation supersedes the earlier offline-only Hanabi status below.

## Current update: Layer2 0.2 (supersedes the 0.1 notes below)

Latest investigation: legacy texture restoration / SRSA LR tool. See
REDELBE_Research/PRIVATE_TEXTURE_RESTORATION.md. Offline proof restores 22 old
G1T resources and 22 LR references for Hanabi/Kokoro and Tifa/Hitomi; 196923 other
material records and 81153 other index entries preserved. Not installed or visually
tested; integration/face-work routing still required. Standalone packages/SRSA_LR
tool passed eight LR bank tests (165 ADPCM + 78 Ogg; eight changed-length tests).
No game files changed during this investigation.

Tina TIN_COS_105 Patriot Bikini crashes when activated (user confirmed).
Crash dump DOA6LR.exe.29492.dmp: native abort 0xc0000409 / fast-fail 7;
underlying C++ exception is invalid vector<T> subscript, via 22d4e90 from
22cc97b. Native model defaults initializer 22ca6e0 caches only costume ID,
so async same-slot model replacement can leave original per-model vectors.
Test fix installed: ASI d734c032ec1224da48268233b92432a7668c48610a6eb3b5ce5a738ba03145a6.
New initializer hook tracks owner/part/request/resource/model identities and
forces only its native cache check to miss on changed model, rebuilding via
the game's own initializer. No bounds checks disabled or mod assets changed.
Build, model-source state tests and 16 KB thread-stack test passed.
IN-GAME RETEST FAILED: user confirmed it still crashes, then paused this work.
Previous ASI/log: research/backups/tina_reload_before_20260916_053853.

Latest preparation fix: actual process-image detection replaces the inaccurate
exclusive-EXE-open test (Steam/readers no longer imply a running game). Tested
read lock, live exact process/PID, other installation and process exit.
Tina's Patriot Bikini OID/MTL tables now validate by their registered resource
types; MTL record bounds are checked instead of requiring equal first bytes.
All 29 current Layer2 mods prepare successfully: 634 payloads / 215 fallbacks.
New generation: sets/20260916_015230_69b28ecf. New mod appearance is not yet verified.

Kashira native costume conversion correction installed: 24 Layer2 mods total.
Minato MNT_COS_011, Momiji MOM_COS_105 and Rachel RAC_COS_005 were previously
left global; now converted automatically from ordinary Kashira Editor packages.
52 ordinary global assets reapplied without those outfits; 522 replacement
payloads / 130 fallback payloads verified. All three model fallbacks match
pristine assets. Live log confirms Minato's Vanilla -> Liza Dress -> Vanilla
model routing; user confirmed both directions work. New launcher prevents duplicate
launches and shows the actual saved preparation error.
Runtime has 635 caption slot names, including Minato. Private texture isolation
is still not installed. See KASHIRA_WORKFLOW.md for exact scope and rollback.

Earlier 21-mod Kashira bridge was user-confirmed: character select, slot names and
F/LT/Back cycling work. 21 marked manager packages and editor projects (483
assets) are in the backup installation. Launcher synchronizes saved project
edits/profile changes against live Kashira indexes; every slot starts Vanilla.
Kashira's DOA6LR library entry now points to the backup copy (prior settings saved).
See `REDELBE_Research/KASHIRA_WORKFLOW.md` for workflow, limits and rollback.
Pre-bridge checkpoint: `REDELBE_Research/backups/kashira_before_20260916_003802`.
Private-texture audit/structural Tina clone are saved but not installed; texture
isolation remains unfinished. No game archive indexes were modified by the bridge.

Caption update installed: native costume-selection caption shows
`Slot: <costume name> Mod: <Vanilla or catalog name>`. 623 verified name mappings,
hexadecimal fallback for unknown slots. User confirmed the labels work great.

Latest change: manual F/Back/LT cycling clears the native body request, allows
300 ms of game cleanup, then reloads with four cache checks bypassed. The user
confirmed outfits now change without leaving the costume slot. All 27 captured
cycles reopened the body model. The user intentionally closed the game afterward.
Build, signature checks, reload deadline/thread/cancellation tests passed.
Current confirmed checkpoint: `REDELBE_Research/backups/layer2_body_reload_confirmed`.
Prior confirmed Random checkpoint: `REDELBE_Research/backups/layer2_random_confirmed`.

Installed only in the `Backup 2026-09-15_210415` game copy.
The user confirmed F, Select/Back, and L2/LT all switch between the normal Ayane
costume and the registered Layer2 mod. Default is selected on startup; payload
files are opened only when selected and requested. The captured log confirms no
replacement opens before the first selection and records all three controls.
The collection now contains 21 mods: 6 on AYA_COS_001 and 15 on AYA_COS_105.
All 483 replacement files and 93 original fallback files passed manifest hash
verification both in the prepared package and the installed test copy.
The 20 additions are experimental ports from the user's local DOA6 collection;
model/texture versions match, but their in-game appearance remains unverified.
See `REDELBE_Research/AYANE_21_MODS.md` for names and mapping limitations.
Selection tests pass for 500 entries, forward/backward wrapping, separate player
and costume state, and explicit random selection.

The latest installed build additionally hooks the game's Random character
selection in offline Versus and Free Training. The first update loaded a match
normally according to the user. The current queue correction prevents activation
of prefetched future results. The user confirmed Random works; the live Versus
log shows Ayane Xmas 2019 queued, activated at the matching character load, and
its replacement assets opened. Free Training is not separately confirmed.
Arcade/Survival opponent preloading is
not enabled. Arbitrary old REDELBE mod compatibility,
two-player resource conflicts, and extended match stability remain incomplete.

Details and exact hashes: `REDELBE_Research/LAYER2_0.2.md`.
Confirmed controls checkpoint: `REDELBE_Research/backups/layer2_controls_confirmed`.
Full pre-random-update backup: `REDELBE_Research/backups/20260915_221651_253`.
Current package: `REDELBE_Research/packages/layer2_ayane_21`.
Backup before adding 20 mods: `REDELBE_Research/backups/20260915_225609_627`.
The normal LR installation's indexes changed externally after the copy was made;
this package is deliberately built and fingerprinted against the copied indexes.

## Historical prototype 0.1 record

## Outcome

**Partial prototype, not a completed REDELBE port.**

- Inspected the supplied archive and both installations; original game preserved.
- Retrieved public REDELBE source and its common dependency. Confirmed substantial
  source/archive correspondence, but the source is a different revision and seven
  required hash-map headers are absent.
- Scanned LR's live code: 7 of 67 original signatures match (3 in Layer2).
- Parsed all 177,352 resource entries across LR's root/system indexes.
- Built `REDELBE_Research/prototype/build/REDELBE_LR.asi` with MSVC x64.
- Generated a 56-asset native-LR Ayane test overlay; all payload hashes round-trip.
- Four offline tests pass, including invalid input and isolated metadata changes.
- With the original loader's self-module-query compatibility behavior adapted,
  the prototype reached the LR 1.10 title screen and logged shadow-index routing.
- Automated key input did not advance the title prompt. Actual costume display,
  offline match, player-two behavior, restart with costumes, and Layer2 unverified.

## Installation state

The original Last Round installation has no experimental loader or overlay.
At the user's request, a complete 7,138-file, 117,025,172,457-byte copy was made
and every file verified by SHA-256. The user then requested prototype installation
into that copy, so it is now the experimental test installation:

`G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415`

Prototype 0.1 and the 56-asset Ayane package are installed there. All 61 package
files and the ASI hash were verified; 22 pre-existing top-level files and the
base index hashes are unchanged. A subsequent test successfully launched this
copied installation with the correct working directory and logged shadow-index
redirection. The user confirmed that Ayane's costume changes in character
selection; the log records the model and 49 other replacement resources being
requested. Match stability and Layer2 remain unverified/unimplemented. Initial installation evidence:
`REDELBE_Research/backups/20260915_211643_637/verification.json`.

## Main files

- `REDELBE_Research/REPORT.md`: evidence, design, compatibility matrix, reproduction.
- `REDELBE_Research/prototype/loader.cpp`: new loader source.
- `REDELBE_Research/prototype/build.cmd`: exact build command.
- `REDELBE_Research/tools/build_overlay.py`: isolated native-ID package builder.
- `REDELBE_Research/tools/deploy_probe.ps1`: scoped install/remove with backups.
- `REDELBE_Research/packages/ayane_full_test`: complete local test package.
- `REDELBE_Research/evidence/overlay_startup.log`: successful title-run log.
- `REDELBE_Research/evidence/title_screen_overlay.png`: observed title screen.
- `REDELBE_Research/analysis/lr_baseline.signatures.json`: runtime pattern results.

## Next executable step

Direct launch of the copied EXE caused Steam to launch the original installation.
A direct Steam launch override fixed the executable path but retained the original
working directory, which prevented resource redirection. Both issues are now fixed
by the adjacent `REDELBE_LR_Launcher.exe`, which starts the official copied EXE with
the copied directory as its working directory and inherits Steam's environment.
Steam's Last Round launch option now points to that launcher followed by `%command%`.
The original launch option was empty; clear it to return to the normal installation.
Configuration backups: `REDELBE_Research/backups/steam_test_launch_20260915_213430`
and `REDELBE_Research/backups/steam_test_launch_20260915_213927`.

Runtime process 37732 was verified with both its executable and working directory
in the test copy. Its log confirmed 57 prepared redirects and the shadow root.rdb
open. Use Steam's Play button for further tests; keep this launch option configured.

The user subsequently confirmed the costume changes. This establishes visible
replacement in character selection, not complete Layer2 or match validation.

Once the copied executable and loader are confirmed running, enter a local mode and select
Ayane's `AYA_COS_001` slot. Confirm that the
log shows the model `data/0x63438245.file` and its textures being redirected, then
visually verify and run an offline match. Removal must use `deploy_probe.ps1`
with `-Action Remove -GamePath` set to the copied installation above.
This removes the ASI/overlay; clear Steam's launch option separately to return to
the original installation. The optional test launcher itself does not patch the game.

This tests native-ID resource replacement only. The original REDELBE folders,
named-file lookup, asset conversion and Layer2 selection hooks need additional
implementation. Do not relabel this prototype as a complete compatible loader.

## User's expected Layer2 interface

Character selection must display character/slot/mod information. Keyboard F cycles
mods; Select/Back cycles backward and L2 (PlayStation) / LT (Xbox) cycles forward,
per the user's requested behavior. Source layer2.cpp has separate DirectInput and
XInput handlers, selection state, UI text updates, and character reload calls.
None of these Layer2 features exists in prototype 0.1. The current Ayane package
is a fixed replacement, not a selectable Layer2 mod.

## 2026-09-17: RC4 hair/head support complete
Main game now runs Raikiri / REDELBE LR 0.3 RC4. Editable title branding was confirmed in RC3. Hair/head Layer2 controls and hair-code captions added; Eve KAS_HAIR_002 and Hanabi KOK_HAIR_001 projects installed in main, both user-confirmed including return to Vanilla. Separate costume and hair/head selections. Standalone Kashira bridge updated. Portable package packages/REDELBE_LR_0.3_RC4.zip; example mods excluded. See REDELBE_Research/HAIR_LAYER2.md and PORTABLE_RELEASE.md.

## 2026-09-17: Crossfade unsuccessful; instant switching restored

Two experimental hair/head crossfade builds produced no fade and regressed
activation until the user changed hair slots. Both were rejected. The exact prior
user-confirmed instant-switch DLL and production sources are restored; installed
and build SHA256 is 33a594cce0084f66881e776707104b741f89f381c367fe6f1aabfc48d99fa4e0.
The main game restarted and reached character select. True crossfade remains
unfinished. Public RC4 ZIP was not updated. Findings and failed-build evidence
are documented in REDELBE_Research/HAIR_CROSSFADE_RESEARCH.md.

## 2026-09-17: Accessories roster visibility confirmed

Main game now hides roster portraits during Accessories, restores them for the
next player's selection or when backing out, and keeps them hidden when both
characters are ready. User confirmed the complete sequence works. Native show/hide
functions resolve by patterns in both saved versions; state tests pass. Installed
DLL SHA256: f54abc7323785d8aac90e346b22eb2469c072d61a5b25fadec1540e71b8d1236.
Instant hair switching remains the base; crossfade experiments remain separate.
Public ZIP unchanged. See REDELBE_Research/ROSTER_VISIBILITY.md.

## 2026-09-18: Normal roster transition confirmed

Roster now plays its full native exit animation when Accessories opens for either
player (parent icon_pos_out plus portrait icon_out). Circle/B resets both poses
and returns the roster instantly. User confirmed both players and instant back
work. Custom fade-in disabled in favor of the requested normal transition.
Installed DLL SHA256: 3f36f77ec82d0e2011e20bb2bc983d8910af3993434f3d647b9fce58d1f66d98.
Evidence: REDELBE_Research/evidence/roster_full_exit_verified.log. Public ZIP unchanged.

## 2026-09-18: Normal Accessories return confirmed

At the user's request, Circle/B from Accessories now plays the normal native
roster return transition (parent icon_pos_in and portrait icon_in), replacing
instant return. Normal exit on opening Accessories remains. User confirmed both
return and exit transitions work. Installed SHA256:
6bcf2a2d1908ed0feac07edb872cd2ee788c95e480693d5617d2477767221317.
Evidence: REDELBE_Research/evidence/roster_return_verified.log. Public ZIP unchanged.

## 2026-09-18: Combined roster transitions confirmed

User confirmed the P1-ready to P2-selection 450 ms fade works alongside native
Accessories exit and Circle/B return animations. Installed DLL SHA256:
1206b40c431f19dc318a6972f1fd6b68262ebc292344e59b8346ae1b88aa2043.
Evidence: REDELBE_Research/evidence/roster_combined_verified.log. Public ZIP unchanged.

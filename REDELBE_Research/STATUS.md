

## 2026-09-18: User settings build installed

Main game dinput8.dll SHA256: dfedd216c99e980854dc311f6511c278b32f840ae9e4d5329d544b67b0670f8f. Checkpoint: REDELBE_LR/install_backups/roster_20260918_131701.

REDELBE_LR/REDELBE.ini exposes 18 supported controls; settings.schema.json catalogs 71 total options, with unported original options explicitly unavailable. Existing branding migrated to REDELBE's L-Raikiri / 0.3 RC4. Fullmix and random_tracks copied as inactive companion configuration. Patches and Optional Extras inventoried in evidence; not installed as executable LR patches.

Parser, roster-state, Layer2-state and four portable installer fixture tests pass. Main-game log confirms settings loaded, expected EXE hash and all hooks initialized. User confirmed the settings build works on 2026-09-18. Alternate instant/native combinations not yet visually confirmed. The package ZIP remains the previous public build; Settings_Kit.zip is a separate settings/launcher metadata kit. Installer source now preserves editable files; the preexisting Sync executable has not been rebuilt.


User requested private branding on 2026-09-18: removed Branding.name/version from installed public INI, template, schema and settings kit. Private branding.ini retained unchanged. Catalog now has 69 entries / 16 supported. Future loader source no longer reads these fields from the public INI; installed DLL remains the user-confirmed settings build. No game restart performed for this configuration-only edit. Parser tests passed.


## 2026-09-18: Optional break-blow restriction patch installed

DLL SHA256 051aa0c1edc46b83d3129c7b13b6849674b26ef27b7fb560f84ce72874f6f66e, checkpoint roster_20260918_133659. Setting Uncensorship.uncensor_loli_blow=true. Runtime log confirms patch enabled at validated updated RVA 0x3aead36. Independent optional patterns validated against both LR builds; mismatch, ambiguity, incorrect call target and already-patched code tests pass. Catalog 69 entries / 17 supported. In-game effect confirmation pending. See BREAK_BLOW_PORT.md.


User confirmed the break-blow restriction patch works for HON/MAR/NIC/SNK and Minato (MNT). Updated public descriptions and removed pending-test wording; no binary change needed.


## 2026-09-18: F5 HUD test build

Main DLL c3d1d7992166ddfae06f59f9281bf4f8f06f4a0ac23594c19ee5dc7e7980e8ad; rollback roster_20260918_135927. UI.enable_hide_battle_hud enabled. State/parser/roster tests pass and startup normal. Visual F5 hide/restore test pending. See BATTLE_HUD.md. Catalog remains 69 entries, now 18 supported. Existing public release ZIP unchanged.


User confirmed the F5 battle HUD toggle works on 2026-09-18. Removed pending-test wording from the installed INI and settings guide; binary remains c3d1d7992166ddfae06f59f9281bf4f8f06f4a0ac23594c19ee5dc7e7980e8ad.


User label preference: use "LR SUPPORTED" rather than "SUPPORTED" for supported options. Updated generator, INI template, settings kit and installed INI. Machine-readable status values remain stable.


## 2026-09-18: Ten-second roster handoff with hover reveal

Installed main DLL SHA256 7040a6ac6751de76a4c943babbc2d70caba8c3fd402c39f10ae9aaca0dee995c. Checkpoint roster_20260918_141419. UI.roster_fade_ms=10000 (range expanded to 100..10000); UI.roster_hover_reveal=true. User clarified appear while highlighted and disappear when moving away, not blinking. Implementation: focused P2 portrait uses full native alpha; leaving sets that portrait alpha to zero and resumes its fade over the remaining duration. All portraits reach native opacity at deadline; icon_select_p2/cos_in_p2 ends fade early. Existing back cancellation, native transitions, F5 HUD and break-blow patch retained. Parser, roster-state and hover timing tests pass. Visual confirmation pending. Catalog 70 entries / 19 supported.

User confirmed the ten-second roster fade and highlighted portrait reveal work. Build 7040a6ac6751de76a4c943babbc2d70caba8c3fd402c39f10ae9aaca0dee995c is now visually confirmed for this behavior.


Custom roster animations master switch clarified: existing UI.character_roster_transitions remains the stable key. True uses custom transitions/fade/hover; false preserves native roster behavior after restart. Runtime review confirms master=false prevents roster state changes and fade startup, leaving hidden=false/fadeAt=0. Metadata now labels On/Off explicitly and retains all dependent controls. No DLL change or game restart needed for these label updates.


## 2026-09-18: Stage slot caption test

Added optional native texture-setter hook for Misc.slot_info_in_sss. Both reference builds have one complete-function masked match at 0x21c1330. Uses the original shared caption pane; strict thumbnail parsing maps Sweat stage_13_1 to S1301GYM, plus the other known stage prefixes. Stage Layer2 loading remains unported, so named stages report Vanilla. Unknown preview IDs clear the previous label to Unknown. Setting off omits the hook; pattern failure skips only this feature. Parser/config tests and combined build pass. Installed SHA256 e344a0d14f863d539d38b37ae944c5146d48623e21539bf8d1cd60ff955fe614; checkpoint roster_20260918_143858. Startup log confirms hook installation. Visual validation pending. Settings catalog now 70 entries / 20 supported; settings kit refreshed, full release package unchanged.

User confirmed stage captions work. Requested Random/fallback label changed to 'Slot: Random Vanilla Stage/Modded Stage'. Parsing tests and combined build pass; installed in main LR. This is wording only; stage Layer2 loading remains unported.

## Colosseum Afternoon stage investigation
User reports a crash with original DOA6 Layer2 DoA Colosseum Aftenoon (E3 Key Art), slot S0401CLS. Read-only audit saved in analysis/colosseum/audit.json; reproducible tools/audit_colosseum_stage.py. Mod replaces resource e12b64ff, Envs_S0401CLS_env.motor.kidsscndb.kidsobjdb. Mod DOK header version 10 / 331 objects / 1,226,228 bytes; installed original baseline v10 / 536 objects; LR baseline v14 / 656 objects / 3,340,320 bytes. Only 51 LR object IDs overlap the mod. Wholesale database replacement is a likely incompatibility, not a confirmed crash stack diagnosis. No game files changed and no runtime crash reproduction yet. Mod package not found by name in main or backup Kashira Mods. Asked user whether crash is original DOA6 or main/backup LR; answer pending. LR runtime currently only captions stages: F cycling excludes stage selection, resource routing only searches costume/hair selections, bridge rejects stage slot IDs. Proper stage Layer2 activation requires these paths plus validated stage-load/reset handling and an LR-native environment port. Do not claim stage Layer2 supported or install the raw old DOK as a fix.

User clarified crash was in main LR after direct injection with backup RDBExplorer.exe; some legacy stages work, most do not. Current resource e12b64ff extracted from main and backup has identical SHA256 11ab82a4bdaa94f75248e380a92dacc0962baede154707c9dc210523e877e85e, 3,340,320 bytes, DOK version 14. Thus the supplied old mod is not currently present at that resource in either base index. Saved exact container offsets and hashes in analysis/colosseum/installed_resources.json. This comparison cannot establish the precise faulting instruction from the earlier crash.

## 2026-09-18: RRPreview / Moka Announcer
Implemented global RRPreview overrides through immutable sync overlay sets. Original DOA6 folder not bulk copied; installed requested Moka SRSA/SRST pair under main REDELBE_LR/RRPreview/Moka Announcer. Streamed Ogg merge preserves LR cue metadata and 26 LR-only voices (802 total); 13 audio streams changed. Pair validation, source Ogg channels/rate, offsets and lengths verified; actual replacement sample counts rebuilt. Self-merge byte-identical, invalid pairs rejected, 5 bridge tests pass. New portable Sync EXE includes names and conversion modules, no runtime dependence on original DOA6/Python/workspace. Main DLL SHA256 db845bee48b04b53a06e34dfdadf1d44b3b3ff8513098b2b28fb32bf0ac3f603; Sync 2382e509f48b56142c395dfb1163b89a811d5d898091c449ba366378121ea828. Checkpoint rrpreview_20260918_150907. Active generation sets/20260918_150910_26c6887d; verified 65 mod assets / 66 Vanilla assets. Runtime log confirms both RRPreview resources opened. Asked user to confirm Moka playback and normal offline match load; pending. See RRPREVIEW.md. Stage/weather work remains deferred.

## 2026-09-18: SRS Audio Studio LR 0.2
Built a new standalone Windows GUI (tools/srs_audio_studio.py), preserving old SRSxtool. Supports preview/extract, MP3/WAV/OGG auto conversion, single replacement, transactional batch by track ID, undo, immutable output folders, and paired SRSA/SRST saving. Uses selected track's channels/rate; new mono MS-ADPCM encoder preserves exact 70-byte block layout (FFmpeg itself only accepts power-of-two blocks). Independent FFmpeg decoder accepted all nine input/target combinations (ADPCM, embedded Ogg, streamed Ogg); unrelated audio and cue metadata preserved, source unchanged, saved banks reopen, invalid files/missing pairs rejected. Encoder sine reconstruction RMS error 24.303 / 32768. Portable GUI manually verified via computer-use, loaded 802 announcer tracks and completed Preview. EXE SHA256 3dbe7e61fdebc0416ef815c86add5d00a3d1a1c543c0b32b8be1579dadc62a40. Installed main game/SRS Audio Studio LR with FFmpeg from user's existing Downloads archive; no game banks changed. Shareable packages/SRS_Audio_Studio_LR_0.2.zip excludes FFmpeg and includes one-time Setup script, README HTML/MD and source. Audacity recommended PCM16 export followed by automatic conversion; manual target settings documented. New edited banks still require game playback checks. Moka prior playback confirmation recorded. Native executable not a from-scratch cue-bank generator; supports existing-bank audio replacement, no loop editing or mixed/stereo ADPCM support.

## Audio test still used Moka — corrected
Root causes: active set still 20260918_150910_26c6887d, plus user saved the workspace comparison bank opened during our GUI test (lr_SE1_Common_SV.srsa); RRPreview silently skipped that unrecognized filename. Backed up and renamed only those two bank files to SE1_Common_SV.srsa/.srst, preserving bytes. New active set 20260918_154550_f110a9d2; compared streams against pristine LR and user bank: exactly ID 0x4aa124ab differs, and its audio exactly matches user's File0204.wav replacement. No Moka modifications remain in active streams. Runtime opens both new RRPreview resources. SRS editor 0.2.1 now canonicalizes known lr_ comparison filenames when saving and reminds users to close/sync after RRPreview changes; standalone Sync now errors on unknown SRSA/SRST names instead of silently ignoring. Filename and paired save/reopen/unknown-name tests pass. Updated installed main-game editor; left currently running workspace 0.2 editor untouched to preserve user's open work. Updated portable ZIP packages/SRS_Audio_Studio_LR_0.2.1.zip. Checkpoint rrpreview_names_20260918_154550. Awaiting user listening confirmation. Reminder: direct Steam launches reuse the prepared overlay; folder changes require Sync or the REDELBE launcher.

## SRS Audio Studio LR 0.2.2 — readable names
Added bank-owned audio names decoded from plain/encrypted record strings; accepts only bounded terminated ASCII whose hash equals the stored ID, with metadata-record fallback and ambiguity rejection. Verified 1,821 audio names across original Moka, LR SV and eight LR voice banks. 0x4aa124ab = sv_system_default_doa6_cappear. UI shows separate hash/readable-name columns, searches both, and selected-track detail shows full name. Exports use 0xHASH__readable_name.ext plus name in tracks.json; batch accepts both named and old hash-only filenames. Filename 0.2.1 canonicalization retained. New module tools/srs_names.py, tests tools/test_srs_names.py pass including malformed pointers/hash mismatch rejection and named extraction. Installed main SRS Audio Studio LR.exe SHA256 678e46d1fab87c682cc0bab941cd7f9f7d2b94f5e00c89a8a90fe6f70d6064a5; old installed executable backed up. Existing workspace 0.2 sessions preserved. Visually verified installed 0.2.2 with user's correctly named test bank; 802 tracks and full cappear name visible. Shareable ZIP packages/SRS_Audio_Studio_LR_0.2.2.zip; no game audio or loader modifications in this change.

## 2026-09-18 SRS Audio Studio LR 0.3.0: tagged original audio library
- New tools/srs_library.py and srs_library_ui.py. Audio library browser reads original RRPreview.rdb read-only, resolves RNK names with existing name fallback, indexes every SRSA and pairs SRST by name. No game audio bundled.
- All 294 banks indexed: 11,880 tracks, no bank errors. Character 8,931; Music 184; SFX 1,989; Announcer 776. Tags inferred from bank names. One bank 0x32c20ade lacks a name, retained under hash.
- Category filter, readable name/character code/hash search, selected preview, selected/filtered extraction, Open bank in editor. Streams read by range for previews. Full-bank editor still loads entire SRST, so large music banks need substantial RAM.
- Added planar 2/4-channel ADPCM decoding to PCM WAV for preview/export. Replacement remains mono ADPCM/Vorbis only.
- test_srs_library.py passed: full index, FFmpeg decode sample per category, planar decoder mono matches independent FFmpeg, 2/4-channel PCM decode, readable filenames/hash manifests. test_srs_names.py passed 1821 names.
- Installed side-by-side main game/SRS Audio Studio LR/SRS Audio Studio LR 0.3.0.exe, SHA256 3c8ece27fe672d0b7d664daf6267d6183d33cc57cd41539c9494e5c649ba0428. Existing editor sessions untouched. Selected archive stored in LOCALAPPDATA/SRS Audio Studio LR/library.json on this PC only. Source archive actual path original game/RRPreview.rdb (not RRPreview/.rdb).
- GUI confirmed full 11,880 row count with 0 bank errors and category selector. Package packages/SRS_Audio_Studio_LR_0.3.0.zip excludes FFmpeg bin/game data; setup scripts included.
- Carries 0.2.3 changes: auto-sync saves directly under REDELBE_LR/RRPreview, Sync RRPreview toolbar, readable-only extract filenames. User's newest 155925 bank was synced into set 20260918_160705_84f53030: all 802 streams matched output, two changed lines. No game listening check after that sync.

## SRS 0.3.1 — clickable column headings
Both library and editor support ascending/descending heading sorting with arrows, numeric hash/duration/rate/channel sort, blank character codes last, selection identity preserved by moving tree items. Sort reapplied after filters/search/refresh. Header double-click no longer starts preview. Tk smoke verified ordering and selection. Built packages/SRS_Audio_Studio_LR_0.3.1.zip and installed main game/SRS Audio Studio LR/SRS Audio Studio LR 0.3.1.exe alongside open versions; launched without closing user sessions.

## SRS 0.3.2 — draggable headings and language filtering
Column heading drag now reorders displaycolumns in both tables; normal click sorts, resizing separators unaffected. Verified Tk mouse press/motion/release moves first column to last, no incidental sort, subsequent click sorts correct moved column, selection retained. Library All/ENG/JP/Other-shared buttons and Language column added. Names-based language markers, unsuffixed character lines inferred JP; 5101 JP, 4521 ENG, 2258 other/shared. Built portable package 0.3.2; installing versioned exe beside existing sessions.

## SRS 0.3.3 — LR-first audio library
LR fdata_package RDB/RDX resources now read directly, range access for uncompressed streams; LR resource names catalog bundled (no game data), missing retail RNK tolerated. All 299 banks /12206 tracks indexed without errors: Character9229 Music185 SFX1990 Announcer802. Added missing Minato bank names. Unnamed LR stream pair matched by record IDs and offsets. Default source auto-detected from installed exe ancestors or saved LR folder, never auto-restores original DOA6. Manual Open DOA6 archive and extracted SRSA options retained. Validated LR category decode, Minato, new TeamNINJA stream, original11880 regression, Tk default-source/ENG filter. Installed main game/SRS Audio Studio LR/SRS Audio Studio LR 0.3.3.exe SHA256 3fb242a3e85a118a0c24b63239ef688925bf60faa3cdbf1cef51572ba70e5f49. Portable ZIP excludes FFmpeg/game data.

## SRS 0.3.4 — default volume matching
Enabled default Match original volume on import, Apply selected, Apply all replacements. Whole-clip RMS constant gain against originally opened bank, peak gain cap0.98, silent skip with status. Input bytes cached session for reproducible rematch; reports saved in manifest; transactional all/import rollback includes caches/reports. Default match applies single/batch. Volume tests passed target within0.3dB and repeated ADPCM rematch stable; 9 format conversion regressions passed unchanged-track/source/save-reopen guards. Built packages/SRS_Audio_Studio_LR_0.3.4.zip; versioned exe installed beside previous sessions.

## SRS 0.3.5 — automatic main-window library
Audio library embedded in main Notebook tab, Bank editor separate tab; normal startup auto-initializes library. Upward ancestor DOA6LR.exe/fdata_package detection works at arbitrary depth, saved LR fallback retained. Explicit SRSA argv selects editor before scan events. Tk verification simulated game/tools/update/mods/mod tools/SRS.exe and loaded12206 rows in main root/library tab. Built portable0.3.5 and installed versioned main-game exe alongside user sessions.

## SRS 0.3.6 — moved EXE crash and direct bank editor
Windows Application events confirmed0.3.5 game-root access violations 0xc0000005 at null. Game folder has proxy winmm.dll/version.dll. Added PyInstaller runtime hook srs_bootstrap.py: SetDefaultDllDirectories SYSTEM32/USER_DIRS, bundle directory registered, explicitly preload system winmm; optional local faulthandler log. Actual built0.3.6 launched directly in LR game root and remained running; loaded modules verified system32 VERSION/winmm. GUI showed12206 library rows, Bank editor802 announcer rows. Preview tested via GUI with root exe and FFmpeg resolved in game/SRS Audio Studio LR/bin. Open bank in editor now uses per-session temp extraction, no output-folder dialog; entering empty Bank editor auto-opens selected or announcer bank. Saved files still require Save new bank. Installed root SRS Audio Studio LR0.3.6.exe, portable ZIP built.

## SRS0.3.7 — editor metadata/filter parity
Added Tag/Character/Language columns and category plus All/ENG/JP/Other-shared filters to Bank editor using same name-based classification as library. Horizontal scroll, sorting/dragging, combined search, visible/total count; reset filters on new bank. Tk test on LR announcer802: ENG364 JP416 other22; combined category exclusion/recovery passed. Built portable0.3.7, installed root and original app subfolder alongside open versions.

## SRS0.3.8 — visible navigation tabs
Main tabs now14pt bold, padded26x12, selected blue/white, inactive pale blue. Uses clam tab element in custom notebook style so Vista theme cannot suppress colors. Actual root-installed GUI checked: large Audio Library/Bank Editor tabs and12206 library tracks. Includes0.3.7 Bank editor filter parity. Portable0.3.8 ZIP built and installed root/app subfolder.

## SRS0.3.10 — important controls enlarged
Large12pt bold Volume, save & activate panel contains matching checkbox, Apply selected/all, wide Save new bank and Sync RRPreview buttons. Removed duplicate small toolbar actions. Default1280x860/min980x740. GUI visually verified all controls visible on root-installed exe with802-track bank. Includes unreleased0.3.9 root/nested Sync detection and Save initial RRPreview directory fix. User confirmed audio works after sync. Active set20260918_174218_1c867baa exact byte comparison matched both saved173843 SRSA/SRST; one changed voice. Portable0.3.10 built/installed.

## SRS0.3.11 — user image icon
Converted supplied Desktop/vlcsnap-2025-03-30-09h24m58s732-Recovered.png to multiresolution16/24/32/48/64/128/256 ICO preserving full image/aspect on transparent square. Source image unchanged. assets/srs.ico embedded into PE and runtime data; Tk default icon plus app taskbar ID set. Portable ZIP includes standalone srs.ico. Installed root and app subfolder0.3.11.

## SRS0.3.12 — larger portrait icon
User requested larger icon; converted original to square close-up crop (90% image height, centered52% width/top4%) filling every ICO size without letterboxing. Embedded exe/window icon rebuilt and installed root/app subfolder.

## Clean public release prepared 2026-09-18
User trigger prepare it for release. Built releases/REDELBE_LR_0.3_RC4_Release.zip. User-facing install/play/sync/remove shortcuts, REDELBE_LR/RRPreview and _Kashira/Mods guides, SRS0.3.12 Tools app, current settings installed from internal payload, notices. Runtime packed into _REDELBE_Runtime/runtime.zip, installer safely expands to temp and delegates tested sync install. No personal mods/audio, caches/logs, development sources, personal branding, old SRS exes, game assets. Required Kashira user-supplied; optional SRS FFmpeg setup download explicitly documented. Exact current game loader/sync/launcher hashes matched. Actual installer/removal with208-file manifest passed isolated space-path fixture, conflicting DLL refused, user project preserved; no personal paths in public text; archive CRC passed. Private verification/staging stays analysis/release_staging; sourcebuilder tools/prepare_clean_release.py and test_clean_release.py. No changes to working game installation. Broader-PC/gameplay testing remains RC limitation.

Expanded release changelog into cumulative loader/Kashira/costume/hair/UI/settings/audio/SRS/install feature inventory with explicit unsupported limits. Updated public release ZIP and SHA256; CRC/content verified. Master changelog releases/REDELBE_LR_CHANGELOG.txt.

User explicitly requested branding.ini in release. Copied installed branding to public REDELBE_LR/branding.ini and internal install payload; manifest209 hashes verified, ZIP CRC/branding exact-match verified, checksum/docs updated. Existing installer preserves installed branding; ZIP extraction upgrade instructions say retain existing branding if desired.

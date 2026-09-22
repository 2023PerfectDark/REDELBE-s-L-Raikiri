# Raidou aura research — incomplete

Request: expose Raidou's persistent red/black mist for all characters through
REDELBE_LR/REDELBE.ini, with later per-Layer2 configuration. No functional toggle
has been installed, and no game code or resource archive was changed in this investigation.

## Evidence

- Live main LR game PID 43920: offline Training, Raidou versus Honoka. Raidou's
  persistent red/black body mist is visible at idle; Honoka has no such mist.
- Original REDELBE source, patches, INI and supplied readmes did not yield an
  existing Raidou aura toggle to port.
- Original RRPreview.rdb RNK names identify separate body, head and limb effects.
  Full original resource-name candidates: analysis/raidou_resources.json.
  Narrow candidates with presence in the saved LR indexes:
  analysis/raidou_aura_candidates.json.
- G1E hashes present in saved LR root index:
  - body aura CE1_EFF_rid_00_body_aura: 0x7fa35bed
  - head aura CE1_EFF_rid_01_head_aura: 0x6360b6f0
  - limb CE1_EFF_rid_02_body_limb: 0xf56f07de
  - separate victory variants also exist; do not substitute these indiscriminately.
- Resource IDs have no literal DWORD references in the saved LR executable image.
  This does not mean they are unused: resource definitions/scripts can reference them.
- Original RID_COS_001.mud and its name database were extracted read-only into
  analysis/raidou_0xe506164b.bin and analysis/raidou_0xdcbd638d.bin.

## Native attachment lead (LR 1.11 research addresses, not runtime constants)

kids::placeable::effect::Attach string RVA 0x4c96828.
Registration at 0x8beef4 selects script wrapper 0x3329570.
The wrapper parses six script integer arguments, resolves effect/model handles
from VM state, validates the effect owner using 0x289f000, then dispatches through
the effect object's vtable +8. This is not a simple (character, effect ID) API.
Calling it with guessed pointers would be invalid.

kids::placeable::level::CreateEffectInstance string RVA 0x4c984a8,
registration references at 0x8d1f94 and 0xa47847.

## Required next work

Trace the actual Raidou spawn/attachment path and effect lifetime in a fresh match.
Identify the persistent effects' owner, attachment bones and cleanup behavior.
Verify applying to another fighter with Raidou absent, round restart, rematch,
character changes and feature disabled. Only then introduce a working INI option
and uniquely validated optional code patterns. Preserve current stage-video and
mouse-menu code in experiments/stage_video; do not replace with older prototype.

Proposed setting (design only, NOT currently implemented):

    [CharacterEffects]
    raidou_aura_all_characters = false

Do not mark LR SUPPORTED until tested. Per-mod Layer2 settings remain future work.

## Follow-up: dedicated aura action found

Read-only live scan (tools/inspect_aura_memory.py) located raw effect definitions
in PID 43920; see analysis/aura_live_scan.json. The definition object hashes are
body 0xc0a1ca5d, head 0xa7a17260, limb 0x85fef54e. These also have no literal
references in the saved executable image.

Searching the original databases by these hashes identified:

- 0x285cb0c3 CE1CommonResource.motor.kidssingletondb: authored effect tracks.
- 0x5ece222a CE1EffectResource.motor.kidsscndb: effect resource definitions.
- 0x97485e9b Field_Common.character.level.kidsobjdb: effect instances.

The dedicated action is CE1ResourceAction[RID_COS_000_ActRID_EFF_ATTACH], object
hash 0x00399961, ActionID 20000. Its DopeSheetObjectNameHashArray has 15 entries:
two body aura tracks, one head track and twelve limb tracks. The tracks include
parent bone IDs, transforms, flags, lifetime/fade and event data, so replacing
only the texture/resource hash is insufficient.

Original action registration is referenced by the Raidou MotorCharacterSetting
record 0xf7c06315 in 0x2082ad97 CE1CommonResource.motor.kidsobjdb. The action is
also in 0xf589e402 Field_Common.character.level.kidsscndb. The only named
EFF_ATTACH actions in the original singleton are Raidou and story Raidou (SRD).

Extracted all five current LR resources into analysis/aura_lr using the current
root.rdb and existing read-only extractor. Parsed the LR motor singleton: all
16 original named records (action plus 15 tracks) remain present; action ID
20000 and 15-track count match. Full decoded records:
analysis/aura_action_records_lr.json. Original records:
analysis/aura_action_records.json. RNK labels come from original DOA6; compare
field hashes, not only labels, if LR introduces/reorders properties.

Tools: find_aura_definitions.py, find_aura_action_references.py,
inspect_aura_action.py. Native immediate-20000 searches did not establish a
verified aura caller. Several matches are unrelated array limits/timeouts.
find_aura_action_code.py and find_aura_action_stores.py are exploratory only.

Likely implementation route: expose/reuse the existing effect-only action for
another fighter, with native attachment and teardown. Do NOT change a fighter's
character identity or replace their main animation/moveset to force this action.
Still unproven whether registering action 20000 in another MotorCharacterSetting
is sufficient; needs controlled test plus caller/lifetime tracing. No INI toggle,
loader binary, game resource, or live process memory was modified in this work.

## Honoka idle experiment, 2026-09-19

Prepared and installed a reversible data-only test appending Raidou's 15 effect
tracks to Honoka idle action 0x0c3844a7 in resources 0x285cb0c3 and 0xf589e402.
User reports NO visible aura. Do not mark this implementation supported.
Builder: tools/build_aura_test.py; installer: tools/install_aura_test.ps1.
Rollback table is recorded in the active package aura_test/rollback_table.txt.

Read-only PID 42872 scan found an unchanged raw Honoka idle record with one
track 0x942e62af. Scan is bounded to the first 4 GiB of readable private memory,
so this does not prove no patched record exists elsewhere. Evidence:
analysis/aura_idle_live_scan.json. The game was restarted with Debug log_virtual,
log_external and log_internal enabled to trace actual resource reads. INI backup:
REDELBE_LR/REDELBE.ini.before_aura_trace. Startup confirms root.rdb redirect;
the two edited resource reads still need checking after entering Training.

Audio: experiments/aura/assets/raidou_aura.wav. Source is user-provided
Desktop 2026.09.19 - 22.04.07.01.mp3. Removed 1.766083 seconds leading silence;
retained exactly 10 seconds, stereo PCM16 48kHz. ffprobe confirms 10.000000.
Audio playback is NOT implemented yet. Game SE getter wrapper 0x37aa350 reads
profile+0x17ebc; setter 0x37aa250 stores controller+0x148 and sets channels 5/6.
These are research RVAs only; production needs validated patterns.

### Archive-backed follow-up
The resource trace loaded the redirected root index but never opened the two
external replacement databases. Prepared tools/build_aura_archive_test.py to
repack a COPY of 0xaf1960fa.fdata, retaining 392 unrelated records and editing
only the two action databases. Recalculates index offsets by resource ID,
preserving preexisting mod index entries. Installed archive_root.rdb and archive
copy under the same aura_test folder; redirected both, no original archive edit.
Awaiting Honoka Training result. Existing rollback_table.txt remains valid.

### Third database found and live patch verified
Read-only scan of LR KOD resources found a third action database 0xd14d76ef
(37,762,232 bytes), in the same 0xaf1960fa.fdata archive. Previous tests did not
patch it. tools/find_lr_idle_databases.py records the three matching resources
in analysis/aura_lr_all_matches.json. Expanded archive experiment to all three.

After restart, PID 56672 raw Honoka idle record at 0x1b7cb339350 contains SIXTEEN
tracks (original one plus all 15 aura tracks), verified by read-only memory scan.
This is the first verified successful load of the modified action record.
Aura action retains 15 tracks. Visual effect/lifetime is still unverified and
requires the requested Honoka Training test. Original archives untouched.

### Static model experiment (unverified)
User confirms no aura with the verified 16-track Honoka idle action. That
approach is not sufficient. Honoka's own idle track uses distinct event data;
Raidou attachment tracks have flag 0xc0002000 and frame 1 event data. Meaning
of these fields has not been established; do not guess them in production.

Found model StaticDopeSheetObjectNameHash column 0xaa117b97, empty uint32 array,
on Honoka model 0xe29b76db. Prepared a new experimental test adding the original
15 aura track hashes to this model field in BOTH resources 0x2082ad97 and
0xc0f49941 (different archives). tools/build_aura_static_test.py preserves other
columns, rebuilds archive copies and index offsets, retains existing mod entries.
Restores original idle actions by building from the original baseline overlay.
Installed copies under active package aura_static; redirects.tsv now points to
root.rdb and two copied archives there. Earlier aura_test/rollback_table.txt is
still the rollback table for restoring the original redirect configuration.
No visual validation yet; this is NOT a supported all-character feature.

Static model test caused or coincided with process exit during startup; no
DOA6LR process remained on verification. Treat as FAILED, do not reinstall.
Restored original redirects.tsv from aura_test/rollback_table.txt, disabled the
three temporary resource Debug logs, relaunched normal configuration. All aura
experiments are now inactive. Next work must establish native effect spawn and
cleanup, not another unverified model-property assignment. Audio still prepared
only, not connected. User-facing aura feature remains incomplete.

## Native trace milestone (2026-09-20 local session continuation)

Confirmed native effect instances and update/attachment chain. NOT a completed
all-character implementation. No loader binary/resource edits this turn.

- Bounded hardware-breakpoint trace in PID 49728 captured 80 calls in 0.11 s,
  covering 15 distinct objects. All reached 0x3402a90 via 0x34029a0 (return RVA
  0x34029c8), called through effect vtable+8 at 0x37f78b0 (return 0x37f78b3).
  Parent routine starts 0x37f7610; pdata splits it into chained ranges.
- Captured objects share effect vtable RVA 0x4be3530. Their +0xa8 resource-wrapper
  pointers group exactly 2 / 1 / 12. Trace: analysis/aura_native_trace.json.
- USER REPORTS GAME CRASHED after this debugger trace. Debugger did restore
  debug registers and detach, but cause is unknown. DO NOT repeat attachment
  until cause understood. tools/trace_aura_native.py is research-only and unsafe
  for further use as-is. User restarted game into PID 21612.
- Continued with read-only OpenProcess/ReadProcessMemory, no debugger. Scan of
  7.66 GB over 45 seconds found 224 effect instances, 19 with nonzero +0xb0.
  Exact identity at [[effect+0xa8]+0x50] confirms 2 x 0xc0a1ca5d body,
  1 x 0xa7a17260 head, 12 x 0x85fef54e limbs, plus four unrelated 0x9027b7e0.
  The exact +0x50 field matters; scanning an arbitrary 1KB chunk finds adjacent
  wrappers and must NOT be used to assign identity.
  Evidence: analysis/aura_effect_instances.json, analysis/aura_active_links.json.
  Read-only tools: scan_aura_effect_instances.py, read_aura_active_links.py.

Native path and fields (research RVAs only; do not hardcode in release):

1. 0x37f7610 effect-controller update receives controller RCX, context RDX,
   additional reference R8, float XMM3. Tests controller byte +0x4c nonzero,
   +0x4d zero, controller+0x50 wrapper nonnull and wrapper+0x20 object nonnull.
2. Effect object = [[controller+0x50]+0x20]; object+0xa0 is runtime descriptor.
   At 0x37f7844 optional controller+0x58 callback is invoked through vtable+8
   with context and controller; it populates transform vectors +0x10/+0x20/+0x30.
   If controller byte+0x4e is zero, calls effect vtable+8 with context->first
   pointer, mode0, index-1, 48-byte transform, final flag false.
3. 0x34029a0 supplies address of effect+0xb0 to core 0x3402a90 as seventh arg.
   0x3402cf0 is alternate wrapper supplying address of effect+0xb8.
4. Core creates attachment record when that pointer is null, requesting pool
   object type0x306e (size0x40) and initializing through 0x2dc9a50. Existing
   records update mode/index and transform. +0xa0 runtime descriptor receives
   mode-specific dispatch. See analysis/aura_attach_disasm.txt.
5. 0x3402db0 is a candidate detach path: releases effect+0xb0 through context
   allocator and clears it. Not hit in the short capture, so teardown/lifetime
   still needs verification. No claim that cleanup was live traced.

Remaining: find creation/ownership of the 0x37f7610 controller and its +0x58
transform callback, tie it to fighter model/bones, establish who sets +0x4c,
+0x4d, then create separate owned instances for another fighter. Preserve
native teardown. Existing action-track and static-model database experiments
remain disabled. Audio remains a prepared 10-second WAV, not implemented.

## Native ownership and startup list resolved (read-only continuation)

PID21612 remained running. No debugger, process writes, DLL changes or archive
changes in this turn. Reverse-pointer scans bounded40s/8GiB.

Live chain verified:
body effect0x1c22cddbc30 <- wrapper0x1c216185220 at+0x20
<- controller0x1c1bc942270 at+0x50. Controller active flag+0x4c=1;
controller+0x40=0xc0a1ca5d, +0x44=0x9db1990b. Controller vtable0x4d31c28;
constructor0x24b23d0. Controller+0x58 callback0x1c1bc942330, callback vtable
0x4d83b90; virtual+8=0x39f0900. Constructor0x294e1b0 (also0x293de90).
Callback+0x48 is fighter0x1c1bc86cc50; +0x50 refcount owner0x1c1bc86cc40.
The callback contains authored transform and bone information (+0x40 bone10).
Evidence aura_controller_live.json and aura_reverse_*.json; these addresses are
session-only and MUST NOT be used in release code.

Static setup path confirmed by direct call references:
0x3a5c610 -> 0x3998bc0 -> 0x399a4d0 -> 0x294e1b0.
The last call constructs the confirmed live bone callback. 0x3998bc0 takes
out-shared-reference RCX, effect descriptor RDX, fighter reference R8, forwards
to manager at global cell0x5e6ef48 (derive/verify RIP before runtime use).
0x399a4d0 converts descriptor effect identifier via0x399b160 /0x399b100 and
constructs/registers native effect controller; full ABI/ownership needs review.

Critical startup source in0x3a5c610:
 fighter+0x78 -> parameter object
 parameter+0x188 /+0x190 -> begin/end persistent-effect descriptors
 fighter+0x130 -> reference passed to effect setup.
Read-only traversal of battle fighter map (cell0x5ea7be8, derived from
0x3a5c4b0) confirms side0 Honoka has EMPTY list; side1 Raidou has1200 bytes =
15 descriptors of80bytes. Matches live aura exactly. Descriptor layout observed:
 +0 bone uint32; +0x10 scale float3; +0x20 quaternion float4;
 +0x30 translation float3; +0x40 logical effect id.
 Padding contains garbage; never copy pointer-looking padding as semantics.
 Logical ids: body0x9db1990b twice, head0x816ef40e once, limb0x137d44fc12times.
 These differ from resolved object ids0xc0a1ca5d/0xa7a17260/0x85fef54e.
 Evidence analysis/aura_fighter_effect_lists.json; tools/read_aura_fighter_lists.py.

This identifies the true native persistent-effect startup list and explains why
idle-action database edits do not activate this system. Next implementation:
validate remaining 0x3a5c610 ownership/teardown and how parameter list is loaded;
add optional per-fighter descriptors through native setup with portable patterns
and correct owned handles. DO NOT globally replace a character's parameters or
identity, call incomplete ABI guesses, or modify shared parameter lists while
another fighter may use them. Existing experiments remain inactive. No INI
feature claimed supported yet; sound remains prepared but not wired.

## Native startup test implemented (isolated development build)
experiments/aura/native_test copied from current stage_video sources, compiled
combined loader successfully. Does NOT edit production stage_video source.
New aura_native_test.h and semantic-only aura_descriptors.h. Restored baseline
archives remain in place. Hook four direct calls to 0x3a5c610; original runs
first, then Player1 only (battle map verified), native persistent list must be
empty and existing fighter-owned weak-reference list empty (avoid duplicates).
Calls 0x3998bc0 with each of15 descriptors and fighter+0x130. Stores successful
weak handles in fighter+0x170 vector, using existing capacity fast path or native
0x2b68710 growth; releases temporary weak reference. Mirrors original weak
ownership bookkeeping. No shared character parameter mutation. Descriptors
zero padding and retain only bone/scale/quaternion/translation/logical effect id.

This test uses current-exe SHA256 and entry byte guards, NOT release-ready
cross-update patterns yet. Enabled separately by REDELBE_LR/aura_test.ini:
[AuraResearch] native_test=1. Installed main dinput8.dll; original backup at
REDELBE_LR/research_backups/before_native_aura/dinput8.dll. Disable by setting
native_test=0 and restarting, or restore that DLL. No debugger attachment.
Need visual Honoka test plus native-created count in log, then round/rematch
teardown tests. Audio still not wired; no public INI support claim.
Native test preflight corrected: two of the four branches are E9 tail jumps, not E8 calls. Verified live bytes and preserved original opcode. Rebuilt and reinstalled; original backup retained.

## User confirms native Honoka aura visible
User: "it crashed on start once then opened normally. the aura is visible on
honoka now". Current PID53320. Log confirms Player1 Honoka vs Player2 Raidou:
107765171 AURA TEST native setup: player 1 effects=15.
Requested next test: Honoka versus non-Raidou opponent, restart round; verify
presence, movement and stability without relying on opponent resource loading.
Do not expand or mark release supported before independence/lifetime tests.

Windows Application log checked 2026-09-19 ~23:18 local: no fresh error1000/1001
for latest reported startup exit. Cause unresolved; do not claim fixed. Earlier
debugger crash DOES have event1000 at22:41:30, exception0x80000004, fault RVA
0x3402a90, PID49728, dump Local/CrashDumps/DOA6LR.exe.49728.dmp. This corroborates
hardware breakpoint exception as crash mechanism, not just generic debugger
incompatibility. Do not rerun trace_aura_native.py. Current native test uses no
debugger. DLL still isolated experiments/aura/native_test and main installed;
production stage_video source unchanged, backup available as previously noted.

## Custom aura sound implemented in native test build
User confirmed Honoka works with non-Raidou opponent and round restart, then
requested custom sound first. Added aura_sound.h in isolated native_test build.
Uses native effect weak-reference lifetime: one additional weak ref to the first
successfully created aura controller, retains no strong ref and does not keep
effect alive. Worker checks strong count; stops/reset output when it reaches0;
new creation changes generation and restarts loop. Old weak ref released on game
startup callback thread; at most one retained control block until next match or
process exit. Module pinned while output worker exists; no debugger involved.

Dedicated waveOut PCM stream, software-scaled samples; never changes global
Windows/device volume or game settings. 3 x50ms buffers, gain ramp perbuffer.
Game SE read at sound-controller+0x148, pointer derived from uniquely validated
0x37aa250 setter pattern (aura_sound_patterns.h, generator script). PCM16 mono/
stereo 8k-96kHz, max60seconds and24MiB; strict RIFF fmt/data bounds checks.
Reads UTF-8 settings from config_entries.h / user_config. Public main INI now:
[AuraSound] enabled=true, file=AuraSounds/raidou_aura.wav, volume=100.
Comments LR TESTING, restart required. Settings added only to isolated test
config_entries.h; promote into settings catalog/generator when integrating
production, not directly overwriting generated release files.

Installed audio experiments/aura/assets/raidou_aura.wav into main
REDELBE_LR/AuraSounds/raidou_aura.wav. Verified PCM16 stereo48kHz duration10s.
Backup before sound at REDELBE_LR/research_backups/before_aura_sound/{dinput8.dll,
REDELBE.ini}. Current native test startup gate still aura_test.ini native_test=1;
visual remains Player1-empty-list test and executable fingerprint guarded.

Build passed existing warnings only. PID46000 startup log:
AURA SOUND configured file=AuraSounds/raidou_aura.wav volume=100
AURA SOUND output ready; PCM loop follows Game SE.
Requested user test: audible loop with Honoka, Game SE response including0%,
and stop on match exit. Audibility and lifecycle are not yet user-verified.

## Aura sound pause correction
The user confirmed playback and Game SE mute, but reported excessive loudness and sound continuing during pause. The isolated native_test build now defaults AuraSound.volume to 50 and the installed INI is set to 50. Native battle::pause (37eb460) sets bit 2 at state+514; battle::resume (37eaf40) clears it. Both resolve the same root cell (5da7620). The audio worker reads current/requested state at +510/+514, pauses its own waveOut stream, and resumes without resetting its loop position. Pausing leaves the queued audio intact. Effect destruction or generation change still resets the stream. No game pause state is written. Masked pause signature is unique; identical resume callbacks are accepted only when their derived root agrees with the unique pause callback. Combined build passes. Installed with backup at REDELBE_LR/research_backups/before_aura_pause. Awaiting user pause/resume verification.

## Explicit-resource independence test
User confirmed quieter audio and pause/resume work. They then reported both visual and audio missing without Raidou on a fresh launch; this supersedes the earlier broad independence interpretation. Existing log recorded effects=15 with Honoka/Marie but no sound start, suggesting returned controllers did not remain active. Factory 399a4d0 resolves descriptor+40 through 399b160 (character/default aliases) and 399b100 (shared aliases), then invokes 37f56b0. Both lookup functions return their input unchanged when absent. The new isolated test copies each descriptor and replaces its logical ID with the known native effect object ID: 9db1990b -> c0a1ca5d, 816ef40e -> a7a17260, 137d44fc -> 85fef54e. This tests bypassing character-dependent alias registration without mutating shared tables. Attachment/weak ownership/audio remain unchanged. Build passed; installed main DLL, previous working sound/pause DLL preserved at research_backups/before_independent_aura. Requires cold-launch Honoka P1 against non-Raidou P2 verification. Resource preloading may still be required; do not claim independence verified yet.

## Independence test failed; diagnostic follow-up
User reports neither aura nor sound with Honoka. Log cold match Honoka (22) vs character11 returned explicit resources effects=0. Static Field_Common.character.level.kidsobjdb confirms 9db1990b is the scene instance record referencing resource definition c0a1ca5d via column0b6e1578. Therefore replacing instance IDs with definition IDs was invalid; alias bypass hypothesis rejected. Restored original 15 scene-instance descriptors and added per-creation resolved/instance/wrapper/effect diagnostics for first three successful effects. Installed and restarted. First launch exited code1 before match, second launch PID28260 reached startup UI. Async question pending: enter offline Honoka P1 vs non-Raidou and leave match running. Need inspect AURA RESOURCE diagnostics and underlying effect resource data before next fix. No debugger or archive changes.

## Missing runtime descriptor confirmed; early-preload test
Creation snapshots in analysis/aura_absent_creation.json show scene instance resolves correctly, effect object vtable4be3530 and resource definition exists, but effect+a0 runtime descriptor=null and controller+4c inactive. Resources at creation have status0fe80003. Do NOT substitute definition IDs. Added bounded early preload callback after existing layer2 loadOriginal: use guarded native37f56b0 for the three scene instance IDs; retain strong refs atomically, disable warm controllers' updates via verified +4d flag, drop temporary weak refs. Hold three resource requests through character loading, then release warm strong refs via native85d830 after real15 attachments at fighter startup. Manager root5e13d60; skip until manager+188 scene exists. No Raidou model or shared character params loaded/modified. Test only, current executable SHA guard remains. Combined build passes. Installed and awaiting fresh Honoka-vs-non-Raidou test. This is a preload hypothesis, not yet verified fix. Cleanup when match startup is cancelled/other characters have native descriptors needs broadening before release; held refs currently bounded to three.

## Early preload disproved, removed
User: still nothing with Honoka. Log shows AURA PRELOAD retained resources=3 at110275234, then15 actual creations at110277531, still no aura/audio. Removed preload callback, warm ref retention and disabled dummy controllers from source and rebuilt/reinstalled baseline+diagnostics. Capture definition runtime via resource+20 (previous resource_data captured +40 metadata instead). Native descriptor preparation found at d4b9b0: calls89fc30 on effect+a8 resource, then gets resource+20 runtime into rbx; engine context+e8 virtual138 (actual310d100 returns engine+38); uses runtime+90 and then1149e20(engineEffectSystem, runtime+78, allocator) to create effect+a0. Need compare captured definition runtime +78 and+90 for non-Raidou vs Raidou matches. These pointers are freed/reused after failure; cannot safely infer their content minutes later from old log addresses. No debugger. Still no fix for Raidou independence. Working audio volume50 and pause handling preserved.

## Comparison pending (2026-09-20)
User said done, but current PID53940 loader.log contains only Honoka22 vs character35, one startup at110538656. Saved analysis/aura_comparison_log.txt. Asked async to enter Honoka versus Raidou without restarting. Non-Raidou definition runtime+78 is null. Resource handler from captured wrapper+18 has RVA7f028d8, vtable4c07d88, preparation callback virtual+d0=9862d0. That callback first checks raw data via efa7c0, then prepares dependency handles at definition+80 and+88 via89fc30 and requires each handle+20 nonnull. Then retrieves raw buffers through efa660/efa6b0/89dc80 and initializes actual effect data via engine context+e8 virtual138 (310d100, returns engine+38); prepared data eventually goes in definition+78. Downstream d4b9b0 takes definition+78 to1149e20 to make instance+a0. Need working Raidou capture to compare raw/dependency handles. No edits or install this turn, current DLL is original descriptors with snapshots, preload experiment removed. Preserve sound volume50/pause behavior.

## Native deferred request test
Raidou match captured in PID53940 at110662218 (Honoka22/Raidou23). Definition+78 populated and audio starts; no-Raidou at110538656 had null+78. Resource-handler preparation9862d0 gates raw loading viaefa7c0 and dependencies+80/+88 via89fc30 before1149d80 creates definition+78. Direct prewarm using immediate wrapper did not solve it. Found native deferred wrapper37f5620, called from399a110 via399a3c0. It invokes37f62a0 with kind1 and autodelete=false, uses manager+190 scene and pending queue+158. Immediate37f56b0 uses kind0, autodelete=true, manager+188 and immediate37f75d0 activation. New test hooks ONLY E8 at399a5ef within399a4d0 through requestEffect dispatcher. Thread-local DeferredScope around the loader's15 custom aura create calls selects37f5620; all other callers retain37f56b0. Native factory still makes bone callbacks and returns weak ownership stored in fighter+170. No custom warm controllers or strong retention. Current SHA/byte/call-target guards retained. Build succeeded and installed; fresh no-Raidou test required. Not claimed fixed. Audio lifecycle may need later refinement if queued effects survive while not yet visibly active; must check match exit and pause after visual validation.

## Deferred path failed; bounded dependency capture installed
User still reports no Honoka aura. PID39684 log confirmed Honoka22 vs35 returned effects=0 through deferred wrapper. Archived analysis/aura_deferred_failed_log.txt. Removed deferred TLS dispatcher and 399a5ef patch entirely; restored original immediate factory path. Added read-only synchronous dependencySnapshot while factory references remain valid: runtime definition handles+80/+88 and bounded 8-node raw dependency list at resource+8; captures node16/raw64, handles128, dependency runtime128. No native calls or pointer mutations in diagnostic helper, all reads checked via ReadProcessMemory. Existing first-three-controller bound retained. Combined build passes with existing warnings. Installed main and restarted. Still NOT an independence fix. Need fresh Honoka/non-Raidou match to identify which raw asset/dependency is absent. No debugger, no shared params edits. Sound volume50/pause code preserved.
Static preparation9862d0 confirmed runtime definition+78 assignment at986574 after1149d80 succeeds. Failure gates raw readiness efa7c0 and runtime dependencies+80/+88, then engine lookup and allocation; raw snapshot needed to distinguish these rather than speculate.

## No-Raidou raw dependency failure captured
Honoka22 vs35 at111482171, user ready. Saved entire log to analysis/aura_missing_raw_log.txt and parsed comparison to analysis/aura_raw_dependency_comparison.json. All15 immediate controllers returned, but first body/head raw nodes of type/hash4d0102ac and b097d41f have NULL data at+10. Working Raidou capture has non-null data for both. Definition+80/+88 both have non-null runtime object pointers, but80 status0fc80001 vs88 0ff80001; nonnull does not prove80 fully prepared. Raw node IDs at+8 are type hashes, not proven RDB fileIDs. Therefore do not try injecting assets using those hashes.
9859b0 resource load callback obtains three raw handles via8a2600 at985cb4/985ce9/985cff, constructs runtime via317d030 and registers dependencies via89f2b0 at9861ba. Preparation9862d0 waits viaefa7c0 then prepares80/88 and creates definition+78. 37f6de0 is DESTRUCTOR, not preload. 37f5730 uses kind0,autodeletefalse, but still immediate37f75d0; do not infer it queues preparation. 37f5620 uses different scene190 and is disproved for current scenario. 89dc80 checks raw data/bitsets and signals ef64e0 when null; does not synchronously return newly loaded data. No further install this turn. Need native loading/registration before battle resource load finishes; repeated startup creation/prewarm insufficient. Existing main game left running, no additional user visual test requested.
Full log also contains earlier working Honoka22/Raidou23 at111440265 in SAME process, then22/35 at111482171. Comparison JSON corrected to group timestamps; all loaded raw pointers belong to earlier Raidou round. Thus assets are unloaded again across matches; once-per-process warming alone cannot suffice.

## Retained pending activation implementation
User requested implementation. Added fixed15 PendingAura strong references in isolated native_test/aura_native_test.h. Original immediate factory still used; inactive returned controllers acquire one strong ref via CAS at control+8, holding their entire dependency graph through resource preparation. Five validated native update call sites (24b52fa,24b550c,24b56cf,24b57c5,37f6cfd ->37f7610) now dispatch through updateEffect with original bool(BYTE*,void*,void*,float) ABI. For matching pending custom objects only, retry native37f75d0 activation every50ms on native update thread. On controller+4c true log AURA READY, begin sound for first descriptor, release extra strong via85d830. Five-second timeout logs dependency snapshots and releases. Native manager retains own strong while callback executes; no object use after removing manager ownership. No worker timer invokes engine APIs. Recursive mutex serializes custom pending array, atomic count gives idle fast path. Native manager destructor sites24b60dd(E9)/24b69f9(E8) ->37f6de0 clear pending refs BEFORE original destruction. First-fighter startup clears old pending when native effects vector empty; all entries bounded15. Sound no longer tracks inactive effects; volume/pause preserved. All hooktargets/opcodes validated before writes under existing executable SHA guard. Combined build passes existing warnings. Installed main after backup research_backups/before_aura_retained_retry/dinput8.dll. This specifically repairs premature controller disposal and retries preparation; no-Raidou asset loading is not yet verified. Previous early-warm test did not retry native activation after creating its dummy controllers, so this differs materially. Must test cold Honoka/non-Raidou match and inspect AURA READY vs LOAD TIMEOUT, then match exit/restart if successful. No change to production stage_video or archives.

## Both-side aura options and Super Saiyan Hayabusa test
User confirmed retained retry works, noted aura applied to all P1 characters (intended former test restriction), requested all characters and mod.ini options; then specifically requested port/test Super Saiyan Hayabusa. Implemented fighterSide map lookup0/1, pending30 tagged byside with per-side startup cleanup, and audio weakControls[2] with shared one-loop OR lifetime. Existing native aura instanceIDs skipped to avoid duplication; other native effects allowed. Global [Aura] enabled true/false read from REDELBE.ini (absent defaultsfalse). Active costume mod.ini overrides global, active hair/head overrides costume. Each Mod records generated table-adjacent iniPath. Stable sidecar REDELBE_LR/Layer2/<exact caption name>/mod.ini overrides generated INI; path component validated. Applied on battle startup, no live CSS toggling. Native Raidou intrinsic aura not disabled by custom flag. Docs experiments/aura/AURA_OPTIONS.md installed main. Compilation passes existing warnings. Production stage_video still unchanged.
Hayabusa source original REDELBE/Layer2/Super Saiyan Hayabusa:7 visual assets.4 absent textureIDs b7c2c648,c7e5818c,2784abbe,ad5d7e7c restored using current LR fallback data and exact current MaterialEditor reference checks. Native hair model format matches except EMPTY16byte EXTR chunk removed; all real model chunks unchanged. tools/prepare_super_saiyan.py outputs packages/super_saiyan_hayabusa_lr_v2 (v1 partial preserved). Combines current installed Hanabi restoration plan with4new references andresources. Installed KashiraProjects/REDELBE_LR_Super_Saiyan_Hayabusa/project.ktproj and _Kashira/Mods/REDELBE LR - Super Saiyan Hayabusa.ktmod. Registered project and combined restoration inbridge.json. Persistent sidecar Layer2/Super Saiyan Hayabusa/mod.ini has [Aura] enabled=true; global main INI [Aura] enabled=false to isolate test to selectedmod. Existing AuraSound enabled/volume50 preserved. tools/install_super_saiyan.py backs up loader/INI/bridge/active pointer before install. Backup research_backups/before_hayabusa_aura_20260920_004857. Native Kashira sync succeeds:7mods,72modassets,73vanillafallbacks; active sets/20260920_004903_88238076. Includes previous RRPreview edit unchanged. RYU_COS_001 slot hashafd1cdf8. User must select mod viaF/LT withRYU_HAIR_001, original expectsRYU_FACE_003. No in-game verification yet; do not claim appearance,aura orsound confirmed onHayabusa/bothplayers. Started main test; watch known first-launch exit.

## Hayabusa face/eye correction
User confirms Hayabusa mod aura/sound works; face/eyes unchanged. Log confirms RYU_FACE_003 hash99377142 so slot correct. Real face base texture table32bd5c11 references CharacterEditor texture contexts: index11 oid7fa2f496 ->0986e48a (eye), index20 oid8b679fda ->70c790ad (skin). Initial port restored MaterialEditor MPR texture contexts only, unused by this face's base path. Added two exact CE databaseb290631c texture property6c7321d2 redirects to existing privateIDs b7c2c648/c7e5818c. Fallback identity verified against current texture resources, no extra resource/mesh changes. Initially considered missinggrp c401b928/oidex537bf650, but those are mesh topology tables (LR differs in submesh count), not texture bindings; did NOT install proposed packages/hayabusa_face_fix/restoration_plan.json or mod.grp. Correct installed plan is character_texture_plan.json. Backup workspace backups/hayabusa_before_face_texture_fix.json. Updated installed project dependencies and workspaceproject copy plus preparation script. Sync validated7mods72assets73fallbacks; active sets/20260920_005922_7f368d6a. Aura loader/sound unchanged, global auraoff, permodon. Pending visual face/eye verification.

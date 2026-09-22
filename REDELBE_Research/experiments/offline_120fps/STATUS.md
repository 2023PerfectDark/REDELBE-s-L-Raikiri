# Offline 120 FPS investigation

Requested: optional 120 FPS in offline modes only; no online PvP changes.
Status: investigation only. No executable, loader, or installed INI changes.

## Findings (2026-09-20)

- Existing hair-color prototype loader contains no frame-rate hook.
- Existing AI Versus route state is driven by UI animations. It is not sufficient
  evidence of the current game mode for a timing override.
- The mapped LR image `analysis/lr_updated.bin` has its own import table;
  `analysis/binary_details.json` target import RVAs do not match this image.
  Parse the image PE imports directly when investigating it.
- Current mapped image imports: Sleep at RVA 0x419b148, performance counter at
  0x419b638. Numerous call sites exist; these are not frame-cap identification.
- Unwind-bounded functions 0x3792590 (0xab bytes) and 0x37db7d0 (0x58 bytes)
  read the performance counter through an object at RIP-relative global
  0x5d4a8c0 and scale/divide by its +0x18 field. Neither is established as a
  rendering limiter. Do not patch these general clock helpers.
- Counter use near 0x2279dad feeds a displayed countdown (PG_font_time);
  not evidence of the render limiter.
- Binary strings DeltaTime, DeltaTimeReal and OneCycleDeltaTime exist;
  their names alone do not prove independent render/simulation timing.

## Required before enabling

1. Identify the render scheduler/present path and the simulation update cadence.
2. Establish an authoritative offline allowlist; unknown/online states retain
   native timing. A route remembered from menu navigation is insufficient.
3. Test 120 distinct rendered frames per second while combat, round timer,
   physics, input windows and audio retain normal speed.
4. Test pause, rematch, mode transitions and restoration before online entry.
5. Only expose an LR SUPPORTED option after these checks pass. An FPS counter
   alone, repeated frames, or doubled game speed does not satisfy the request.

## Continued static investigation

- Added `inspect_timing.py`, a read-only mapped-PE reference analyzer. It uses
  executable sections, unwind function bounds, and decoded instruction boundaries
  to filter byte-search candidates. Output remains research-only.
- `frame_sync_refs.json`: FrameSync references at 0xa11430 / 0xd42790 initialize
  reflection descriptors. Their common vtable at 0x4c2c048 is metadata machinery,
  not a verified scheduler. FrameSyncType names belong to animation properties.
- FramePerSecond reflection enumerators: 0xac7340 and 0xac7600; descriptor tables
  at 0x4bdfbc8 and 0x4bdfb10. These still need tracing to a live timing owner.
- `sleep_refs.json`: decoded call-site inventory. Examined 0xf04f80: its Sleep(0)
  occurs in a statistics callback lock loop, not a frame limiter. 0x11a5f90 is
  resource/random-data initialization with a lock, also not a limiter.
- `timing_constant_refs.json`: 458 candidate scalar references to 60, 120,
  1/60 and 1/120. These are not patch sites. The double-precision 1/60 consumers
  at 0x14c8c52 and 0x14cb36e convert elapsed time to indices and update vectors;
  they do not establish frame pacing. Shared constants must not be changed.
- `mode::unlocked_game_mode` is a scripting binding name at 0x4934408; it does
  not establish the current offline/online match state.

No playable 120 FPS build yet. Next investigation must identify the presentation
path and measure its relationship to simulation updates, rather than treating
property names or generic wait/clock calls as proof of an FPS cap.

## Live Training check — 2026-09-21

User opened offline Training. `probe_mode.py` performed query/read-only access
to PID 43188 (main installation). No memory writes, hooks or timing changes.

- Native `network::is_online_versus` callback at 0x39165a0 tests
  `*global(0x5da8e48) + 0x8f8 < 5`. Seven equivalent inlined predicates resolve
  to the same global; all seven live byte sequences were checked before reading.
- Ranked predicate at 0x37eb1a0 compares mode with 0; lobby at 0x37eb340 compares
  with 1. In this offline Training session the field is 255. This is evidence of
  a non-online state, NOT a verified offline game-mode allowlist.
- `scene::get_v_sync_num` callback 0x23c6190 reads the scene manager global
  0x5dfffa8, field +0xa0.
- Scene update 0x2279cb0 reads its second argument's +0x10 integer, calculates
  integer 60/value (or 1 for zero), stores +0xa0, forces zero results to 1,
  then advances the scene counter at +0x118 by that value.
- Live 8.0020689-second sample: 480 scene ticks, 59.9845 ticks/second; sampled
  step was always 1 (772 reads). This is a scene counter, not a rendered-FPS
  measurement. The probe checks that the scene owner remains stable.
- Therefore changing that FPS input to 120 alone leaves the step at 1. It does
  not produce a half-size update. Render/scene separation must be established
  before a 120-Hz scheduler change; generic clock or constant patches remain
  inappropriate.
- Present-named render pass at 0x311d410 dispatches through 0x310a9f0 or
  0x310ab80, with backend submission at 0x12fe580. These are leads, not verified
  DXGI swap-chain Present hooks or proven timing control points.

Implementation status remains explicit: read-only diagnostic tools implemented;
120 FPS runtime support NOT implemented or installed. Current game unchanged.

## Scheduler investigation and experimental build — 2026-09-21

An isolated tracing loader was built in `native_test`. It changes no timing,
observes scene-update arguments, and calls the original update once per call.
Three launches exited early, including one where the observer declined to install.
No scene telemetry was captured. These results do not establish the cause of the
startup exits. The tracing build is NOT suitable for installation.

Restored `rollback/dinput8_before_trace.dll`, SHA256
918AA66279C314785484CEA11FFC409661FB19B6048D305A547ED3E2DFAB5CE1.
The restored game stayed running (PID 50204); no active-set changes were made.

Native application global: 0x5da7620. Accessors at 0x372c074 and 0x372bfd4
independently resolve it. `probe_mode.py` now verifies their live code before
reading the application's timing fields, and requests only query/read access.
Live observation on PID 50204:
- +540 / +544 = 60 / 60
- +548 = 1
- +54c / +550 = 60 / 60
- +554 = 0, +558 = 1, +55c = 0.0166666675, +560 = 1
- +564..566 = 1, 1, 1
- Scene counter: 301 ticks / 5.0096428 seconds (60.0841 ticks/sec).
This is NOT rendered FPS, nor an offline mode allowlist validation.

Scheduler/preparation function 0x372c290 (ends 0x372c80a):
- Copies requested +544 into +540, and +550 into +54c.
- Computes max(1, +540/+54c) into graphics context +1d6.
- Computes +55c from scale +558 divided by +540.
- Supplies +540 and scale to the native frame-data constructor 0x20131a0.
- Native update wrapper 0x3730020 supplies the same fields to 0x372dba0.
- 0x372dba0 calls multiple managers, including 0x3728480, which calls the scene
  update 0x2279cb0. Skipping only the scene update does not establish that all
  gameplay simulation remains at normal speed.
- Setters 0x372c060 (+544) and 0x372bfc0 (+550) have inlined equivalents.
- Native code at 0x39fe773 sets +550 to 30; 0x39fddb2 restores its default.
  Trace these for render-cadence behavior next. Raising +550 above +540 leaves
  the integer quotient at its minimum of 1, so a simple rate write is insufficient
  evidence of 120 rendered frames/sec.

Static evidence: scheduler.txt, app_global_refs.json, app_update_refs.json,
game_update_refs.json, scene_update_refs.json. FPS setter direct-reference scan
was empty; inlined stores were found through application-global references.

Still NOT implemented: playable offline-only 120 FPS support. No FPS settings
were enabled in the user's INI and no executable/timing patches were installed.

# Hair/head crossfade — both experiments failed; stable build restored

## Latest result (September 17)

Both experimental builds failed user testing: no fade, and hair mods required
switching to another hair slot and back to activate. Candidate 2 also marked the
outgoing request cancelled, but this did not fix activation. Neither is suitable
for release.

The exact previously confirmed instant-switch DLL and its production source and
pattern header have been restored. Installed and build DLL SHA256:
`33a594cce0084f66881e776707104b741f89f381c367fe6f1aabfc48d99fa4e0`.
The installed ownership manifest matches. The main game was restarted and reached
character select. This restored build has **no crossfade**.

Evidence: `evidence/crossfade_candidate1.log` and
`evidence/crossfade_candidate2.log`. Candidate 2 is archived under
`experiments/hair_crossfade_candidate2/`. Experimental headers remain unused by
production source; renderer pattern generation requires `--crossfade-experimental`.

The render hook recorded zero outgoing/incoming model draws. Its first argument
was a static module object, not either heap-allocated hair/head model. Thus the
alpha field below is not yet connected to the actual preview draw path. Retaining
loading requests also appears to interfere with replacement resource loading;
this is an inference from the activation regression, not a proven cache mechanism.
Further work needs the actual preview rendering path and safe visual-instance
ownership independent of the retained loading requests.

Clock, selection, and pattern tests passed, but did not validate native rendering
or replacement behavior. Public RC4 archive remains unchanged.

## Historical candidate 1 notes (superseded by results above)

Requested behavior: retain the outgoing hair/head while the incoming mod loads,
then fade outgoing opacity from 1 to 0 and incoming opacity from 0 to 1.
Reverse this when selecting Vanilla. Keep the body visible and unchanged.

The earlier instant-switch experiment was user-confirmed working, but had **no
fade**. A new crossfade candidate was installed on September 17 at 21:47 and
subsequently failed visual testing. Do not ship it.

## Current candidate

- `prototype/layer2_crossfade_runtime.h` retains the old hair and face request
  handles while replacements load, then applies a 350 ms smooth opacity ramp.
- The request ownership is moved out before calling the normal request path, so
  the old request is not immediately marked cancelled. Cleanup uses the native
  release function; no game allocation is freed by the loader directly.
- The native render callback multiplies model instance `+0xa8` by the transition
  weight and restores it after that model's render call. This field feeds
  `xmm13` at updated RVA `0x302bcdd`, participates in transparent-pass selection,
  and multiplies shader alpha. It is separate from animation time.
- Live preview models have vtable RVA `0x426f7a0`; request `+0x68` points to this
  class. Both hair and face use the same class, with separate instances.
- Render entry old `0x302b780`, updated `0x302b730`; the complete 41,188-byte
  relocation-masked function matches uniquely in both snapshots. The wrapper
  forwards all 17 native arguments. No fixed RVA is used in the loader.
- Incoming readiness starts the timer; 5-second timeout, next cycle, natural
  slot request, detail-menu exit, and match load retire the retained handles.
- Logs include BEGIN, READY, and END with outgoing/incoming render counts.

Build SHA256: `44dad4a06a1b49a1f5e4c4050cd0c3e0a01be163f30985cb58f8d2f20136c482`.
Main rollback checkpoint:
`REDELBE_LR/install_backups/crossfade_20260917_214733`.
The installed-files manifest was updated for this test binary; the public RC4
archive has not changed.

Validation passed: crossfade clock tests, existing Layer2 selection tests, and
native pattern tests against both snapshots including rejection of modified and
ambiguous code. Visual testing of retained rendering and material blending is
still required. Main game successfully reached title animation with the hook.

## Verified from the saved Ver. 1.11 mapped image

- `0x22cbfd0` returns request `+0x68` for the requested preview part.
  Owner handles: part 0 at `+0x70`, part 1 at `+0x38`, part 2 at `+0`.
  Handles use a shared control block whose strong count is at `+8`.
- `0x2d579f0` writes animation time/frame at `+0x24`; it is not opacity.
- String `kids::placeable::model::EnqPropertiesWithTransparency` is at
  `0x4c970a0`. Registration at `0x8c4ee0` stores callback `0x3336e80`.
  The generic registration object's vtable methods are not renderer functions.
- Callback `0x3336e80` parses three integer script arguments. The first two
  locate a script model; the third is passed in `r8d` to `0x3017140`, with
  `r9d=1`. Further inspection shows the third integer is a property hash, not a
  literal opacity value: the renderer resolves it and requires float type
  `0x08000001` before obtaining the float value.
- `0x3017140` uses an auxiliary object at model `+0x1c8`, allocating `0x204`
  bytes if absent, then calls `0x326da80`.
- `0x326da80` appends a 16-byte record to a queue capped at 32 records. Record
  contents: `0`, supplied integer, `0xffffffff`, supplied flag. This does not
  establish an alpha setter and must not be invoked on preview pointers based
  only on its name.
- Direct branch references found: `0x3017140` only from the script callback;
  `0x326da80` only from the enqueue wrapper. No demonstrated connection to the
  character-select preview render objects yet.
- The normal request replacement path marks the old request byte `+0xc=1`.
  Holding a shared reference alone therefore does not prove the outgoing model
  will remain submitted, animated, or visible.

## Remaining verification

1. Confirm outgoing and incoming models are both submitted during the ramp.
2. Visually check blending and depth behavior of Eve and Hanabi materials.
3. Exercise rapid cycling, character/menu changes, and match entry for cleanup.
4. Verify both players and returning to Vanilla before packaging a release.

Read-only helper: `tools/crossfade_xrefs.py RVA...` prints direct branches and
stored pointers to functions in the saved updated image.

Do not claim that the experimental binary is packaged as a public release.

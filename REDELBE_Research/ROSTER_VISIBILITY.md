# Character-select roster visibility

September 17 build; user-confirmed visual behavior in the main game.

Requested sequence confirmed by the user: hide the roster during Accessories;
restore it after Player 1 confirms so Player 2 can choose; keep it hidden once
both are ready. Returning to costume or character selection restores the roster.

## Implementation

- Roster portrait layout: `0xf403bcba`, repeated native layout instances.
- Accessories: `0xdd6728d2`, `detail_in` hides portraits.
- Portrait `icon_on_p1`, `icon_on_p2`, or initial `icon_in` restores portraits.
- Costume layout `0xb384f573`, `cos_in_p1`/`cos_in_p2` restores on cancellation.
- `detail_out` alone leaves visibility unchanged; confirming the final player
  must not reveal the roster. Loop animations do not restore it.
- Native show/hide functions are signature-resolved, RVA `0x21bd100` and
  `0x21bd430` in both saved builds. They handle single and repeated instances.
  The hide routine clears visibility in every matching repeated-layout node.
- A show hook prevents native show requests from overriding the hidden state.
  No character resources, input handling, or model reload behavior is changed.

Implementation: `prototype/layer2_roster.h` and `prototype/layer2_runtime.h`.
Native observations: `evidence/roster_trace.log`.

## Verification

User confirmed: "All of that works" for hiding during Accessories, restoring for
Player 2, staying hidden after both confirmations, and restoring when backing out.
Runtime evidence saved as `evidence/roster_verified.log`.

State tests pass for Accessories, next player, final confirmation, cancellation,
scene reentry, and unrelated layouts. Existing pattern validation passes against
both saved executable versions, including changed and ambiguous code rejection.
Build succeeds with the existing export warnings.

Installed candidate SHA256:
`f54abc7323785d8aac90e346b22eb2469c072d61a5b25fadec1540e71b8d1236`.
Original instant-switch rollback DLL is in main-game
`REDELBE_LR/install_backups/roster_20260917_220812`.
The later `roster_20260917_221041` checkpoint contains the tracing DLL.
Public release ZIP has not been updated.

## Entrance-animation follow-up (failed visual test)

User requested a fade when the roster returns, retaining instant return on
Circle/B. Candidate replays the native `icon_in` animation for the portrait
instance IDs observed during the scene's original entrance, when hidden portraits
are restored by `icon_on_p2`. Costume/back navigation uses immediate visibility.
Recent XInput B or keyboard Escape input also suppresses the entrance replay.
No new native function or opacity-memory offset is introduced.

Candidate SHA256: `e7e7b37092e020950d7db5f906c3c57fa53b1d6b1a96e150dd0de98a8c70db60`.
Backup of the confirmed instant roster build:
`REDELBE_LR/install_backups/roster_20260917_221621` in the main game.
Build passed, but user reported "Forward still pops in". Replaying `icon_in`
is insufficient. Evidence: `evidence/roster_native_entrance_failed.log`.

## Color-getter opacity test (Player 1 handoff confirmed)

Native layout lookup `0x21c3e20` returns the loaded layout for each previously
observed roster instance. Live image panes have owning layout at `+0xd8`, and
their color getter `0x172fd00` returns vertex color from `+0x160+vertex*4`.
Both functions match uniquely in the old and updated snapshots.
Candidate scales the returned alpha byte over 450 ms for those layouts only;
it makes no persistent pane-color edits. B/Escape cancels the ramp immediately.
Counter `UI ROSTER fade color reads` checks whether this getter is used during
the visible transition. Runtime recorded 35 resolved layouts and over 11,000
color reads per fade. User subsequently confirmed a fade when Player 1 is ready,
and requested a different Player 2 transition while Accessories remains open.
Exact Player 2 sequence is being clarified; no additional behavior changed yet.

Installed SHA256: `9acceb69f6907595182d1df9d91ca3d5330632731bf58be0ae434bfe89e5e4e5`.
Latest checkpoint `roster_20260917_222649` contains failed entrance replay build.
Confirmed instant roster rollback remains `roster_20260917_221621`.

## Player 2 portrait-only native exit (failed user test)

User clarified the requested animation is the normal EXIT before stage select,
played while Player 2 Accessories remains open. Candidate plays `icon_out` on
the observed portrait instances on P2 `detail_in`, waits for native animation
completion, then hides the layout. P1 still uses the confirmed alpha fade on
handoff. Native `animationReset` (0x21bf270) restores the `icon_out` starting
pose before showing on back navigation; `animationPlaying` (0x21bf3d0) checks
completion. Both functions match uniquely in both saved versions. Existing
pattern rejection and roster state tests pass. Visual exit/reset behavior still
needs confirmation.

Installed SHA256: `fe313f5f91253e79d5cb0897716e77dccbb91eaf4fc90f89700e8e7868357899`.
Checkpoint `roster_20260917_223638` contains the confirmed P1-fade build.
No public package updated.

## September 18: Full normal exit on Accessories entry (confirmed)

User reported the previous build still broken and requested the normal transition
when Accessories appears. The previous test played only portrait `icon_out`,
omitting the parent `0xbbf9987c` / `icon_pos_out` seen in the game's normal exit.
New candidate runs both on `detail_in`, for either player. It captures the parent
instance argument from the native `icon_pos_in` event instead of guessing it.
Completion waits for both parent and portrait animations. Back-navigation resets
both exit animations to their initial poses and shows portraits immediately.
Custom fade-in is disabled for this normal-transition test.

Build passed. Installed SHA256:
`3f36f77ec82d0e2011e20bb2bc983d8910af3993434f3d647b9fce58d1f66d98`.
Checkpoint: `roster_20260918_124547` (contains previous failed exit candidate).
Last confirmed basic instant roster build remains `roster_20260917_221621`.
User confirmed: "Both players and instant back work". Evidence saved as
`evidence/roster_full_exit_verified.log`. Public ZIP unchanged.

## Normal return from Accessories (confirmed)

User now requested the normal stage-select-back entrance instead of instant
return on Circle/B in Accessories. Candidate detects the return to costume
selection, cancels outstanding roster exit, resets outgoing animation state,
and resets/plays parent `icon_pos_in` plus every portrait `icon_in`. Normal
exit on reopening Accessories is retained. Player handoff behavior is unchanged.

Build passed. Installed SHA256:
`6bcf2a2d1908ed0feac07edb872cd2ee788c95e480693d5617d2477767221317`.
Checkpoint `roster_20260918_125057` contains the confirmed full-exit/instant-back
build. User confirmed: "Return and exit transitions both work".
Evidence: `evidence/roster_return_verified.log`. Public ZIP unchanged.

## Player 1 handoff fade restored (confirmed)

User requested removal of the instant pop when P1 confirms and P2 starts choosing.
Re-enabled the previously confirmed 450 ms alpha ramp specifically when hidden
roster receives `icon_on_p2` after P1 Accessories. Native Accessories exit and
Circle/B entrance paths are retained. Build passed and installed SHA256:
`1206b40c431f19dc318a6972f1fd6b68262ebc292344e59b8346ae1b88aa2043`.
Checkpoint `roster_20260918_125552` contains the confirmed native return/exit build.
User confirmed "it works" for the combined build. Evidence saved as
`evidence/roster_combined_verified.log`. Public ZIP unchanged.


## Ten-second handoff / cursor reveal test build

2026-09-18: User requested 10 seconds after Player 1 ready, with portraits appearing while the P2 D-pad cursor highlights them and disappearing on departure. New settings: roster_fade_ms=10000; roster_hover_reveal=true. Renderer uses existing validated color hook and per-instance layout lookup. Native icon_on_p2/icon_off_p2 events track the focused portrait. Departed portraits fade from zero over the time remaining, while untouched portraits follow the normal overall fade. Focus changes do not restart the timer. P2 selection terminates fade; back handling stays as before. Timing and state tests pass, visual test pending. Rollback main install_backups/roster_20260918_141419.

User confirmed the ten-second handoff fade and cursor-controlled portrait reveal work on 2026-09-18.

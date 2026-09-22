# Hair color research — 2026-09-20

## User objective
Add a Hair Color selection entry in DOA Central, independent of PS4 packages,
with actual recoloring and per-custom-slot settings. This is **not complete**.

## Implemented prototype
- `native_test/hair_texture.h`: PC G1T BC1/2/3/7 and RGBA/BGRA albedo decoder,
  recoloring to RGBA8 while retaining every mip and alpha byte. Rejects unsupported
  array textures and inconsistent payload lengths.
- `check_texture.py`: verified 5,505,024 alpha values across three mip levels of
  Kokoro's 2048x2048 BC7 hair albedo. Generated file is 22,020,152 bytes.
- `catalog_hair.py`: finds name-based candidates in MaterialEditor XML. These
  are candidates, not proof of exclusive material ownership. Hair ties excluded.
- `prepare_preview.py`: copies an existing prepared package into a new directory,
  adds precomputed colors for 12 Hitomi/Kokoro hair slots (8 distinct albedos),
  and retains existing Layer2 resources and private-resource entries.
- `native_test/hair_color_menu.h`: experimental owned-window palette, **not a
  native KSCL menu tab**. Default, Blonde, Red, Blue, Silver, Pink, Black. Prototype
  choices stored in `REDELBE_LR/HairColors.prototype.ini` by character/custom slot.

## Native findings
LR 1.11 has names for the PS4-style functions but availability returns false,
get_hair_color returns zero, and color setters are no-ops. A temporary availability
probe exposed no usable control and was restored. No ticket/ownership/save patches.
The native custom-slot getter reports the main-fighter slot rather than the
currently edited slot. The installed build instead tracks the native
`cursor_slot_in/loop/sel/sel_after` events, with their bounded instance index.
The obsolete getter resolver has been removed from source.

## Verified in game
- Hitomi Hachimaki: Blonde, Red, Blue and Default apply immediately.
- White headband, face and outfit visually retained.
- Palette entry is at the bottom of the custom-slot details card. Mouse opens,
  applies and closes it. Right-click returns to native slot selection.
- Fresh launch restores saved Blue when opening Hitomi Slot 1.
- Slot 2 starts Default, saves Red, and Slot 1 still restores Blue independently.
- Controller and keyboard bindings are implemented but not physically tested.

## Resource ownership audit
`audit_catalog.py` verified 92 named hair material objects against the binary
MaterialEditor DB, referencing 56 distinct resources. 73 objects use a texture
that is also referenced by material objects outside the narrow hair-name filter.
This does not prove that those other references are body/accessory materials;
it does prove that a global resource replacement cannot be assumed isolated.
Some references differ from the older XML (e.g. PHF_HAIR_004). The audit records
the current binary value and the older XML value separately. Results are in
`audited_catalog.json`; no additional resources were installed from this audit.

## Still required
- Replace the temporary palette with a native menu entry, or clearly agree on an
  overlay design. Verify controller navigation and resolution/fullscreen behavior.
- Verify texture ownership and isolation for all supported characters/hairstyles.
- Verify mod precedence: explicit Layer2 replacements now take precedence in
  source/installed loader, but this still needs an in-game hair-mod check.
- Apply saved choices in matches with correct player/custom-slot identity. Current
  routing is restricted to the DOA Central test context.
- Integrate preparation into the portable bridge without external research XML.
- Use pattern resolution throughout, validate version changes, update public docs.

## Test installation and rollback
Main game's `dinput8.dll` and `REDELBE_LR/active_package.txt` backed up in `rollback/`.
Original DLL SHA256: `5CD842B39EE5D9FB8F2618165A3577EB33C198DF6C89F0619A70A69C9F66FB83`.
Original active package: `sets/20260920_014054_accdcbff`.
Test package: `sets/hair_color_research_01`. Original game archives were not edited.
Restore both backed-up files with the game closed to remove the test.

## Dependency
Texture decoding uses bcdec: https://github.com/iOrange/bcdec . Source and license
are under `native_test/third_party/`; no external decoder runtime required.

## 16-color roster expansion — 2026-09-21 (not active)

Implemented the requested palette in `palette.json` and the C++ selection UI:
Default, Black, Dark Brown, Light Brown, Dark Blonde, Platinum Blonde, Silver,
White, Bright Red, Orange, Yellow, Lime Green, Cyan, Royal Blue, Purple, Pink.
Colors are approximations of the requested tones, not extracted PS4 swatches.
The palette is now a 4-by-4 grid. D-pad and arrow keys navigate both axes.
Existing seven-color saves migrate through an explicit index map into Colors16;
old Colors entries remain available to the rollback build.

`prepare_preview.py` now verifies named hair objects against the current binary
MaterialEditor rather than trusting older XML resource references. It generated
840 variants (56 albedos times 15 colors; Default uses original assets), covering
92 hairstyles / 24 character codes. Container signatures, sizes and IDs passed
for all 840; alpha consistency between all 15 variants passed for all 56 albedos.
Generated payloads total 16,639,056,000 bytes before copied existing package data.
Shared texture isolation and match routing remain unresolved. This is NOT full
roster support and not proof that non-hair materials remain visually unchanged.

Compiled loader SHA256:
3259C779BC2A0DA281F56FDF9221F38C81E7C5EAF69E96FD9F967F7C6C64A367.
Build succeeds with existing warnings. First launch stalled before creating a
window; second launch exited through the previously observed startup path.
No in-game verification of the new grid or expanded character scope occurred.

Restored loader and package selector from `rollback/palette16_before/`.
Restored DLL SHA256:
918AA66279C314785484CEA11FFC409661FB19B6048D305A547ED3E2DFAB5CE1.
Active package restored to sets/hair_color_research_01.
The expanded set remains at sets/hair_palette16_roster_01 but is NOT selected.
Workspace package: prepared_palette16_roster. Do not distribute this test.

Remaining: diagnose startup failure, verify grid in game, finish missing character
resource mapping and shared-material isolation, then verify saved colors in matches.

## Installed again at user request — 2026-09-21

The complete palette16 build is now ACTIVE in the main installation:
- DLL SHA256 3259C779BC2A0DA281F56FDF9221F38C81E7C5EAF69E96FD9F967F7C6C64A367
- Package sets/hair_palette16_roster_01

Mixed tests (new DLL/old package and old DLL/new package) both exited at startup.
A subsequent DIRECT launch of DOA6LR.exe with the game folder as WorkingDirectory
reached the main menu (PID 27272), confirmed by menu logs and a screenshot.
This successful run does not establish that intermittent startup failures are
fixed or prove why direct launch succeeded. No timing workaround was added.
User is testing the 16-choice palette and a newly covered character next.
Rollback remains available in rollback/palette16_before. The earlier note that
this set is not selected is superseded by this installation entry.

## Hairstyle menu and persistence update — 2026-09-21

User confirmed colors change, but reported they do not stay saved. Existing
Colors16 entries were present in HairColors.prototype.ini. The old resource
selector was gated by palette visibility and editor screen 6, so leaving that
screen stopped routing recolored textures even though values had been written.

Installed DLL SHA256:
51FEA54D05A86C99BE673DA7AB805EF48F45FD653ACA05F2493357FC1AF27B86.
- Palette prompt restricted to Hairstyle list (screen 0, family 8f2023d0).
- Footer prompt: [X / Square / G] Select Hair Color, left of Rotate Character.
- G uses a shared rising-edge poll so controller-primary input can still use it;
  DI G is swallowed while the palette is available. X replaces the old Y binding.
- Mouse hover selects grid focus, click applies, wheel moves by row, right-click
  closes. Footer click opens. This remains an owned-window overlay, not native UI.
- Color routing uses wardrobe context independent of prompt visibility. Context
  includes slot list/details and wardrobe hair/costume/glasses families.
- Save keys now include character, custom slot and hair hash. Existing Colors16
  slot keys and old Colors choices serve as migration fallbacks. Writes and readback
  are checked, with failures logged rather than silently claiming a successful save.
- Match routing / per-player isolation remain unfinished; this does not claim
  saved colors are applied in matches.

Build passed with existing warnings. Installed and direct-launched the main game.
Awaiting in-game confirmation of prompt placement, controls and re-entry persistence.
Rollback DLL: rollback/palette16_before_hairstyle_menu.dll.
INI backup: rollback/colors_before_hairstyle_menu.ini.

Follow-up: automated launches of 51FEA54D... exited before the title screen through
same startup path, including a direct elevated launch. No new menu screenshot or
persistence test could be obtained. The user-requested test build remains installed;
user asked to launch via their normal method and report controls and persistence.
Do not describe this build's menu behavior or save fix as verified in game yet.

## User clarification and confirmed loader fault — 2026-09-21

User reports color disappears in Character Select / matches, not just wardrobe.
Colors16 INI has per-hair entries and logs confirm saved values reloaded in the
wardrobe. This is the known missing match routing, not evidence of failed INI
writes. Do not present the wardrobe persistence change as a match-color fix.

Windows Application event 1000, 2026-09-21 01:06:54:
DOA6LR.exe access violation 0xc0000005 in DINPUT8.dll offset 0x44baa,
DLL PE timestamp 0x6ab0b4ca. Exact backup palette16_before_hairstyle_menu.dll
has this timestamp. Fault is `lock cmpxchg dword ptr [rdx+8],ebx` in the aura
sound worker, during the active weak-control scan. Time coincides with our
Alt+F4 before installation. Confirmed loader teardown fault, NOT attribution of
the separate startup ExitProcess(1) failures.

Source aura_sound.h now uses a checked ReadProcessMemory snapshot instead of an
interlocked write to probe a weak control's strong count. Inaccessible controls
are retired from the worker. Build passed. This guards the recorded invalid
access, but does not prove all lifetime issues or startup failures fixed.
This newly built DLL is NOT yet installed; the running/install target remains
51FEA54D05A86C99BE673DA7AB805EF48F45FD653ACA05F2493357FC1AF27B86.
No loader-disabled A/B startup test has been performed in this turn.
Next: controlled loader/no-loader startup comparison; investigate native object
lifetime fully; implement custom-slot and per-player match hair-color routing.

## Aura guard installed at user request — 2026-09-21

Installed main-game dinput8.dll SHA256:
FC8F22D5D001921F9BAD0C2EB0EAFAA2994B38A125F493DFBD5583C9C3EFCDCF.
Verified installed hash equals the compiled binary. Prior installed DLL preserved
as rollback/before_aura_guard_20260921.dll (51FEA54D...). Package selection and
user configuration unchanged. Direct launch requested after installation.
This installs the checked aura control read; no match hair-color support or
proven fix for unrelated startup exits is claimed.

## Startup ordering and audio shutdown fix — 2026-09-21

Installed main dinput8.dll SHA256:
C996B3BD823E192047C4B69BEDBA9F61A31F62C8D16F4E8D959C7AAA6EC5070E.

- Resource/startup IAT hooks now installed after catalog loading but BEFORE
  native feature hooks. Previously the game could perform its module query
  before the compatibility import hook was installed. This is a timing-based
  diagnosis supported by repeat launches, not a captured causal trace.
- Aura worker now has a stop flag and retained thread handle. The ExitProcess
  hook requests shutdown and waits up to two seconds before process teardown.
  Existing checked native-control reads remain. No join occurs in DllMain.
- Temporary resource-only diagnostic branch defaults off and its test INI has
  been moved out of the game. All features remain enabled; active package and
  user settings are unchanged.
- Original guard DLL preserved in rollback/before_shutdown_fix.dll and
  rollback/aura_guard_from_startup_test.dll.

Evidence: event 1000 at 01:38:04 mapped to PRE-GUARD DLL timestamp 6ab0bb3b,
offset 4547a: lock cmpxchg through stale aura control. It is not a new failure
of the installed guard. Full guard/shutdown builds with old ordering still
exited code 1 before title. Loader-disabled interactive launch reached title.
The earlier hidden launch test is inconclusive; its main thread was in normal
GetMessage loop, not evidence of an independent vanilla startup hang.

Resource-only test omitted l2 catalog and hit a native breakpoint faec4f;
this test is invalid for attributing the original failure, because redirected
indexes require catalog-backed loose file resolution. Catalog order corrected.

After ordering fix: PIDs 54316 and 48676 reached title loop b281b468 and closed
using Alt+F4 without new Application error events. Logs startup_order_pass1.log
and startup_order_pass2.log saved. Third run PID 19856 reached startup layouts;
third run subsequently reached b281b468 title loop; saved startup_order_pass3.log.
No offline aura match or hair
color match routing verification in this turn. Animation browser remains on hold.

## Player color binding test — 2026-09-21, awaiting user verification

User confirmed affected case is Honoka Custom Slot 1 (internal slot 0).
Read-only selection snapshot: character 0024a639, costume afce789f,
face bc2e0ee7, hair a4db76ed, native hair color -1. Saved color exists.

Installed test DLL SHA256:
AF435F8BA6998D4F4DB2B2A79F0AFE8F106AE06DC0AC8B0294F97C2F73F1DCEA.
Rollback: rollback/before_player_color_binding.dll (C996B3BD startup fix).

Changes: optional unique full-function pattern for native get_hair_hash;
thread-local observation of character/custom-slot/hair and timestamp. Model
request binds the saved Colors16 value when observation matches character/hair
and is less than one second old; otherwise an unchanged binding is retained,
or an unknown new selection uses default. No guessed slot-zero fallback.
Outside wardrobe, resource routing considers both bound players. Conflicting
colors for the same resource return vanilla; true per-instance texture isolation
is still required for those cases. Explicit Layer2 textures retain precedence.
Resource selector locks l2 mutex around reading hair routing state.

This is an UNVERIFIED test, not complete general match support. Need to verify
the getter is called on the same thread close to real selection requests (and
not just a list enumeration), cache refresh when changing custom slots, and
battle-load persistence. User asked to test Honoka Slot 1 after fresh launch
without opening DOA Central, then offline match. Keep startup-order and audio
shutdown fixes; do not revert them to address unrelated color issues.

## Honoka broken-hair inheritance test

User confirms saved-color selection/match test works. Break Blow switches half-up
HON_HAIR_001 (b658706c, albedo be13d543) to long HON_HAIR_002
(a4db76ed, albedo 1531c622), which reverted to default. Requested half-up
Platinum Blonde -> damaged long Platinum Blonde, while separately selected long
remains saved Cyan.

Installed test SHA256 980E824746A354E5BB2186C4FF90BD8AFDE9A4457F7D2260FE43C6118026AD19.
Rollback DLL before_break_hair_inheritance.dll; saved INI colors_before_break_hair.ini.
On native match load, mark matching hair bindings as battle-active; outside the
wardrobe also route the declared damaged-hair albedo using the source player's
color. A new preview request clears that side's battle flag. No INI values are
modified by damage inheritance. Only Honoka 001->002 relationship is implemented.
Shared-resource conflicts across players still fail to vanilla; cache behavior
and actual Break Blow visual result need user verification. Build passed.

## Roster-wide battle hair color inheritance (2026-09-21)

User confirmed Honoka half-up Platinum Blonde remains Platinum Blonde when broken,
while separately selected long hair keeps its saved Cyan.
Extended the same runtime behavior to all currently prepared palette characters.
Instead of guessing native source/damage pairs, initialization groups validated
hair_colors.tsv entries by explicit character code. During match loading, any
prepared hair texture from that fighter's group inherits the selected hairstyle's
color. Wardrobe and normal selection still use the individual saved hairstyle.
No extra native hooks or saved-setting mutations were added.

Coverage: 92 hairstyles, 24 characters. This does not add missing palette assets.
Existing shared-texture/different-player-color conflicts still fall back to vanilla.
Build passed. Compiled harness using the actual select() implementation passed 442
within-character routes plus independent long-hair selection, wardrobe precedence,
and conflicting-player checks. Installed in main game and restarted; live log
confirms initialization with 24 characters / 92 hairstyles. Roster-wide visual
Break Blow testing remains unverified beyond the user's Honoka confirmation.
Installed SHA256: 80E97576D1D76B767ACF2DBC5F85E201C0E8D2BF00493C0832D26992063BCA56
Rollback: rollback/before_roster_break_hair.dll

## Expanded current-resource catalog and prompt styling (2026-09-21)

Corrected the earlier claim of roster coverage: the 24 codes were the old catalog,
not the game's complete roster. expand_catalog.py resolves named material objects
against the current binary MaterialEditor. Object hashes use signed UTF-8 bytes.
Also probes current MNT names absent from the old CSV. prepare_expansion.py resolves
KTID object references through current CharacterEditor before matching verified
hair-only albedos. Excludes accessory names, face/skin atlases and unknown textures.
Raidou's separately named FACE hair albedo is explicitly routed for his hair slots.

Installed 355 hair slots / 31 internal codes. Includes NPC codes MPP/SKD, so this
is NOT a claim of 31 playable characters or complete 32-character support.
Mai's six hairstyles, Momiji, Rachel, Kula, Minato and many shared variants now
have catalog entries. Unresolved named headwear slots are recorded in
expanded_palette_assets/coverage.json (Bayman, Rig, Zack). Base short hair embedded
in face atlases still needs a verified pixel mask or material-specific solution.
Current scope is stock texture coverage; arbitrary Layer2 meshes are not guaranteed.

510 new recolored containers validated (resource ID, container and G1T sizes).
8,103 generated route checks passed with actual selector code, plus independent
saved hair selection / wardrobe precedence / cross-player conflict fallback.
Built and installed DLL SHA256:
3939A0C8A55FADFB4E829B8046A49389A0104FC89A35062570321DEB9CB5D9AC
Rollback manifests/DLL: rollback/before_palette_expansion/
Installed into current sets/hair_palette16_roster_01; prior manifests preserved.
No save choice modifications. Restart log confirms 355 hairstyles initialized.

Collapsed prompt now uses transparent color-key background, 24px normal white Arial
text styled to the observed native footer, graphical monochrome Square and blue Xbox
X plus G key, positioned beside Rotate Character. Icons are recreated vector glyphs,
not extracted Sony/Xbox/native game assets. Expanded palette retains 18px text to
avoid long color names overflowing. Visual and Mai Bride in-game test pending.

## Wardrobe mouse and Tamaki secondary layer test (2026-09-21)

User requested left-drag rotation, Back recovery, and complete Tamaki coloring.
Observed Asymmetrical Wave with Pink main hair but teal front strand. Live request
and screenshot confirm LR internal SKD code is Tamaki (earlier notes incorrectly
called SKD an NPC; do not reuse that assumption). SKD_HAIR_001 uses two verified
hair albedos: 98e61888 plus 406f95ea (hair_a_BLEND). Catalog regex now recognizes
letter-suffixed hair layers without matching hair accessories. Current material
references also reveal Momiji's secondary 50517fe9 albedo. Generated 15 variants
for both, installed manifests, vanilla fallback and overlays, validated Tamaki's
001/011/031 mappings and Pink/Cyan/Platinum Blonde containers.

Reproduced Back from Custom Slot to Wardrobe Character: f30929e8 out disables
mouse active, while native portrait cursor resumes with no fresh icon_on/loop.
The mychara_on event is the favorite marker, NOT current selection. Fix saves the
last actual portrait focus and refreshes portrait panes only when leaving screen5
on f30929e8 out. Child lists leave screen6 and do not take this return path.
250ms pulse delay prevents carrying Back to the parent menu.

Left-drag within preview area (outside lists/footer) now translates horizontal
motion to native LB/RB rotation in the existing XInput mouse path. Small movement
threshold, 45ms expiry, immediate reversal/release. Palette/modal/focus loss/menu
changes/physical button input reset gesture. Unit test from actual rotationStep
passed direction, expiry, reversal and release. Keyboard-only rotation path still
needs native rotate key mapping; no guessed keyboard scan codes were added.

Build passed, installed DLL SHA256:
E375CB42D731DC81F1541E873E44ABE6388D5A47380D889470D0C68E294F3104
Rollback: rollback/before_wardrobe_mouse_tamaki/ (DLL and package manifests).
First launch exited code1 at native RVA57257701, before UI; no Windows Application
Error event recorded. Second launch reached UI, PID20044. Do not claim startup
reliability fixed from this test. User interaction checks pending.

## Wardrobe rotation pointer lock (2026-09-21)

User requests cursor lock while rotating and investigation of vertical camera.
Added anchor in client coordinates on drag start. Each active poll consumes
horizontal delta then returns pointer to the anchor and resets the delta origin.
Release, menu/modal/palette switch, outside-client detection or foreground loss
ends rotation. Does not globally ClipCursor, so no persistent OS confinement is
left behind after game exit. Build passed; installed SHA256:
8202CEF2AF9FEA948350DCF39AB9905FFADB504A53C9DD25EC11CBB811C780A5
Rollback: rollback/before_rotation_pointer_lock.dll. Restarted normally.

Vertical camera not implemented. Read-only executable investigation found general
kids::placeable::camera::ApplyCameraOffset / Orbit / SetEyeAt bindings, with xrefs
saved in wardrobe_camera_candidates.json. These are generic engine interfaces;
the live wardrobe camera identity/ownership and native update overwrite behavior
are not established. No camera writes or broad free-camera patch were installed.

## Vertical dragging model trace (2026-09-21)
Added bounded read-only WARDROBE MODEL logging to existing modelDefaultsHook, only on changed model sources in Wardrobe. Logs owner/request/resource/model for each part, maximum 48 records. Build passed. Installed DLL SHA256 8D55CA324E49B2F77B298A2AED437569AB4233159F72BFB81D346454BBB6D8D6; rollback before_wardrobe_vertical_trace.dll. Game restarted; user asked to open Custom Slot. Vertical movement NOT implemented or enabled. Native SetWorldPosition script wrapper RVA336d6b0 invokes actual object's virtual +70 at336d7be; coordinate vector at rsp+30. Do not call script wrapper with guessed arguments or change every placeable object.

## Live Wardrobe position identification (2026-09-21)
PID24332, module base7ff702080000, owner7ff707e82f08 captured from modelDefaults. Body model2a5a8b30030, face2a5a8af38c0, hair2a5a8b0e640. Body vtable RVA426f7a0: virtual20=300aaa0 AddWorldPosition, virtual70=303e5a0 SetWorldPosition. Verified disassembly: setter writes x/y/z at +18/+1c/+20 for unparented model and invokes invalidation. All three +1c0 parent fields zero. Body/face positions match and change during idle (~-5.26,116.92,-0.03); hair local position zero. Therefore do not assume static baseline or blindly translate three models: determine update ordering/attachment before movement hook. Vertical dragging still not implemented; diagnostic DLL remains installed.

## Vertical drag prototype installed
Compiled and installed C51A58C4FBED7FADF45B286BAB5CFB515A8D52EB3EF73F4ACB5B20187C4E3980. mouse_menu.h accumulates vertical mouse displacement at 0.15 world units per logical pixel, clamps +/-80, resets outside wardrobePreview. modelDefaults publishes Wardrobe owner. Optional unique function-boundary signature resolves native SetWorldPosition (303e5a0 in current binary); hook adds Y offset only to live body/face/hair pointers read through that owner. Ordinary rotation remains. No saved-data changes. Rollback before_vertical_drag_prototype.dll. Actual setter callback frequency and visible result NOT verified; user in-game test required. If no movement, inspect alternate transform update path, do not claim success from compilation.

Vertical drag root-only correction: live part2(owner+0) position=(0,80,0), part0/1 both ~(-1.93,272.49,3.68). Indicates derived attachment transforms receive duplicate offset. Apply offset ONLY request at owner+0 (loop part2), preserve native derived positions for other requests. Range increased +/-200, sensitivity .30 per logical pixel to permit full head/feet positioning. Compiled and installed; visual confirmation pending. This is inferred attachment ordering, not fully traced.

## Local ticket system foundation (2026-09-21)
User approved optional hair-color unlocks with possible other mod cosmetics later. Added native_test/ticket_wallet.h and ticket_storage.h plus test_ticket_wallet.cpp/.cmd. Wallet balance capped at1,000,000; generic namespaced unlock keys; purchases spend once; failed persistence rolls back in-memory transaction; strict versioned ledger parser; flushed pending file then MoveFileEx replacement. Actual filesystem roundtrip, invalid input, insufficient funds, duplicate purchase, failed save and overflow tests pass. Intended defaults:1 ticket per offline Versus win,5 per permanent hair-color unlock, hair-color gating optional. NOT connected to match hooks or hair UI, NOT installed, no tickets currently awarded. Next: independent match result consumer (avoid dependence on VersusPatternParts enabled), wallet runtime initialization/mutex, UI balance/purchase prompt and optional config/schema entries, reward dedup tests. Preserve free existing hair colors and game save; do not touch platform ticket APIs. Native premium_ticket functions are mostly disabled stubs; this is local mod currency.

## Local tickets first integration installed
Installed FE9A4DBFB4BBB21CBE7BF79845C0B4EE83AEA8A1B6BF082CE7581BCEC79205DE, rollback before_local_tickets.dll. ticket_runtime.h uses separate LocalTickets.dat, strict load disables on corruption. Hooks existing patternparts result consumer; P1 offline Versus win awards1 by default, loss/no change none. Reward hooks install when Tickets enabled even if parts disabled; native parts untouched when disabled. Hair menu shows balance and prices for locked colors; optional purchase keyed character+hairstyle+color, cost5. Tickets.hair_color_unlocks false by default preserves free coloring, default color alwaysfree. New config entries and installed INI section. Wallet persistence/failed-write/reward duplicate tests and config tests pass; combined build passes. Restarted game. In-game win reward and purchase NOT yet verified. GUI schema entries and richer insufficient-balance feedback pending. Unlock purchase persists before hair setting write: if hair settings write fails, permanent unlock remains owned and retries cost nothing. Only P1 Versus currently supported; other offline modes and P2 human rewards unimplemented.

## Wardrobe ticket balance display installed
Added ticket_display.h: click-through owned nonactivating overlay, TICKETS + wallet balance beside coins at logical1920 coordinates410,142 size290x40; font Arial bold italic27, dark translucent background. sync called before pumpHairColor early return, visible for wardrobePreview (character/custom-slot/detail lists), gated Tickets.enabled. Hides on focus loss/leave; updates100ms. Existing hair palette balance retained. Build passed. Installed D1BA7F4CAA9ADBD740B1CA7A8B1B5D24642DE165624158134DA1C769D05B95B1; rollback before_wardrobe_ticket_display.dll. Restarted. Visual position awaiting user confirmation; this is overlay, not native restored ticket pane.

## Premium Ticket asset comparison and icon build
Read-only comparison output analysis/ticket_comparison/comparison.json. Original ScreenLayout.rdb versus LR root.rdb: ticket_period.g1t/texinfo, ticket_info.texinfo and ticket_info_External_00.g1t/texinfo identical; ticket_info.g1t same617324 size differenthash; both KSCLs differ. Decoded LR_ticket_rgba image8 is actual red Premium Ticket icon (64x64). Added ticket_icon_data.h premultiplied embedded pixels and AlphaBlend icon to ticket_display.h. Build passed. NOT installed: initial close not finished; subsequent close interrupted by user input and Wait-Process timed out PID42840. Existing game DLL unchanged (D1BA7F4C...). New build available native_test/build/dinput8.dll. Need normal game close before copy. Preserve rollback before_native_ticket_icon.dll if not exists.

Native ticket icon build installed and SHA256 verified72F4BD920329DD14F71408C90F26BF086ADA42CFA8D52493DBE71B9247A63765. Rollback before_native_ticket_icon.dll. Game restarted. Visual placement still awaiting in-game confirmation.

Icon-only ticket labels installed SHA2568860FC6F3920DD0FF24AE0C981D1CC80CB9D6922EA39A3667D607404A8FA598F. Shared ticket_icon.h uses thread-local GDI assets. Removed Wardrobe TICKETS label and hair-palette Tickets: text; both balances use native icon+number. Locked colors when ticket gating enabled show Name: icon price, wrap price to second line for long names. Free/default/owned colors no price. Pricing settings unchanged. Build passed, restarted; layout not visually verified yet. Rollback before_ticket_icon_labels.dll.

Ticket reward notification installed7ECFEB6C5CC7580C63C8BC34DD7444AAE2E6BAEF960C310B79A27A3C5C0E3472. After wallet award successfully persists, publishes amount and8second deadline. Existing click-through balance window shows You won + original ticket icon + earned amount at lowercenter(815,900 logical1920), outsideWardrobe. No extra award path; uses existing deduplicated P1offlineVersus reward. Build and wallet/reward tests pass. Rollback before_ticket_win_message.dll. Visual reward timing/position not verified in match yet. Overlay remains timerbased, not native pattern-reward layout insertion.

Wardrobe custom UI voice installed F45419613B831C978D6695DD5BBDFAF2BF8EB88C677DB997BA9AB610C57F6DF1. wardrobe_voice.h uniquely resolves native dub getter via runtime function signature and reads validated settings pointer; ENG 8ddfa68d, JP 6eeaefc2 verified with live user settings. Hair palette closed-to-open edge plays nv_us_doa6_kas_12 or nv_doa6_kas_12 once. WAVs from LR banks under REDELBE_LR/Audio/Wardrobe; portable paths, no personal paths. Build passed. Rollback before_wardrobe_voice.dll. Uses async PlaySound separate from native Voices mixer; in-game cue confirmation pending. Future custom panels must call shared wardrobevoice::sync entry API.
User confirmed both Japanese and English Wardrobe entry voice cues work. Runtime log separately shows JP started and ENG started on panel entry.
Update Info voice build installed C4C3715E8883F98CD00155C15E6669275372ABA292B18C9F110F613EADAE3479. Native layout 84b536e1 information_in triggers dub-matched Kasumi line16 once, information_out rearms. ENG/JP clips extracted from LR NV Kasumi banks and converted PCM WAV. Hair-color line12 unchanged. Build passed; in-game audible verification pending. Rollback before_update_info_voice.dll.
Correction: 84b536e1 information_in is MAIN MENU NOTICE, wrong trigger per user. User close/reopen patch notes trace confirms df867d44 in/out is actual Update Info window. Changed trigger to df867d44 in, reset out. Corrected build installed 1F171FB1047EEFAE823CC18018AE20966E73E5858E235ABB544E79364B318A9B; verification pending.
User confirmed corrected Update Info voice works. Log verifies ENG and JP line16 on df867d44 window opening and reopening, no cue on main menu information_in.
Editable update notice prototype installed: update_notice.h reads UTF-8 REDELBE_LR/update_info.txt; update_info.ini [UpdateInfo] ShowEveryLaunch=1 schedules native right-thumb input after main menu settles 1.5s. Test text [REDELBE LR Update ver. Alpha 152] / Ayane: Testing. Runtime confirms auto request opens df867d44 and titleTextHook receives native patch notes, replacing text. Await visual user check. Current limitation auto injection only works via controller path (keyboard mapping pending); replacement recognizes English Update Info or 1.11 (must generalize). Rollback before_update_notice.dll.
Update notice sequence test installed DD8BDD30F7BA9DFD8AAE750EF401A54444CCBF50E3DF8DA6A521C99B06D071CB. Custom REDELBE page then native developer page after out via delayed right-stick input. Developer text preserved. Close label replaced with Dont show again until next game update; eff_select+out saves per-page executable hash in update_info_state.ini, custom notice content digest additionally rearms REDELBE updates. Back intended no persistence (requires user verification). Current caveat developer followup not yet respecting developer dismissal; auto-opening remains controller-only. Rollback before_update_notice_sequence.dll. Visual, sequence, dismissal validation pending.
Refined notice sequence installed 41923F35FFB10E2940C72EC04EBCE49C192F0AA29C897A7EB5AE0F2E6B82A1F2. Automatic sequence respects independent developer dismissal. Manual openings start custom notes again then original developer notes. User confirmed orange label fully visible. test_update_notice.cmd passes actual-header state transitions, preserved developer text, dismiss-on-confirm vs close without eff_select, restart suppression, game digest invalidation and changelog content invalidation (hash helper mocked in unit test). Restart persistence visual check pending.
Back dismissal fix installed DFF17F47A4099CA0CAE9E9CBB13183E54ABC5ACAEA894B6C76DE59B8734BFAD3. update_notice::buttons maps Back to native confirm-close with saveRequested false; only actual confirm input may persist on eff_select/out. Controller, keyboard confirm/back and right mouse back integrated. Holds swallowed once close requested. Tests now exercise Back->eff_select without saving, actual A confirmation saves. Unit tests and build passed. Test dismissal state cleared, game restarted, user verification pending. Rollback before_update_back_fix.dll.
Live log confirms two complete notice sequences dismissed with Back on both pages. All four show Back: close without saving; update_info_state.ini remains only [Dismissed], no saved keys. User verbal confirmation still pending.
User confirmed Back fix works. Bracket color test installed 82125DFD0B58DB711F1052EE624E73851436242244A3594ACBE175A436A9C6E0. Native ^00~GREEN~/YELLOW~/DEFAULT~ markers wrap complete square-bracket sections in custom notice only. Captures current native text setter args; pump refreshes color every700ms while REDELBE window open, clears target on out. This is two-color alternation, not smooth interpolation. Body and developer text untouched. Unit tests cover multiple/unclosed brackets, build passed. Visual confirmation pending. Rollback before_notice_color_pulse.dll.
User confirmed REDELBE bracketed text yellow/green color alternation works in game.
Birthday feature installed B8560A269A87D549711D850AE6486871CA539B1D023E7877058BD3441406F12C. birthdays.ini lists32 roster entries,31 dates including Nyotengu November19 by explicit user request, Phase4 blank unknown. birthdays.h uses GetLocalTime only once at loader launch; no network/current-date server. Birthdays bypass update dismissal and ShowEveryLaunch=0, reuse REDELBE-first page with native body greeting plus large58px logical overlay birthday_display.h. Ordinary dev notes unchanged. Birthday Close does not save update dismissal. Parser tests valid/shared/invalid/leap-day/disabled and previous notice tests pass; build passed. Large-text placement NOT live visually verified on birthday; current date may have no match. Sources saved Birthday list and sources.txt. Rollback before_birthday_notice.dll.
Nyotengu bilingual special message installed 9774D8396EE4B861326B9E8653B4D1C186C7B9F05788C280BEAE51C5BD69A4EB. Exact user EN/JP copy in editable BirthdayMessages/Nyotengu.txt UTF8; Nov19+Nyotengu matched triggers override and Congratulations Nyotengu large heading. Calendar remains local GetLocalTime only. Tests cover wrong day, right day, disabled/no matching fighter, existing notice behavior; build passed. Translation/layout unverified (user will test later). Native notice replacement still identifies English [Update Info] source text; other UI languages need separate mapping/testing, do not claim localized support. Rollback before_nyotengu_special_message.dll.
Momiji birthday image test installed 728C882B8909A050DD91539F1BADD4D09D697A61670B55738EED8147B9F5A0E7. Original user JPG copied unchanged to BirthdayMessages/Momiji.jpg. birthdays::momijiBanner requires local9/20 plus matching enabled Momiji. birthday_display loads JPEG via GDI+, renders preserved16:9 image below58px heading in REDELBE-only overlay; gate remains inWindow&&!developerPage. Developer assets untouched. Build passed. Placement and developer-page transition awaiting visual test. Rollback before_momiji_banner.dll.
Momiji banner correction installed 8FBF0B760CB3C9F1DAAA3C602071BD74D24E8103930452CFD70C043022511A20. User screenshot identifies native wide banner at logical1920 centered1024x334,y130. Overlay moved there, fills rectangle with aspect-preserving cropped JPG (vertical crop30percent). Uses opaque alpha255 and offscreen memoryDC single BitBlt; timer only repaints on position/size/visibility changes, removing20Hz erase/repaint flashing. Still REDELBE-page-only; dev assets untouched. Build passed, live visual verification pending.
User confirmed corrected Momiji birthday banner covers original without flashing and original banner returns for developer notes.
Mila banner installed 34AA43CF5D6A8B67AFC04FD2D643FC9F78A3A99D5A91395444D32C978048C0EC. BirthdayMessages/Mila.jpg copied unchanged from user source. Generic bannerFile selected for Momiji local9/20 or Mila local10/4 plus enabled matching fighter; same user-validated opaque buffered rectangle rendering, REDELBE-page-only. Build passed, game restarted, visual confirmation pending. Rollback before_mila_banner.dll.
User explicitly requested pretend October4 2026 because changing system date disrupted Steam. Added opt-in birthday_preview.ini [BirthdayPreview] Date=2026-10-04, installed active. Only birthday calendar overridden; Windows date untouched. Clear Date and restart to restore GetLocalTime. Do not ship active preview in release. Build passed. Mila visual test pending.
User confirmed Mila birthday banner works. At explicit user request cleared installed birthday_preview.ini Date=. Normal GetLocalTime resumes on next game launch; current process caches prior preview until restarted.

# Mouse menu support research â€” 2026-09-18

Requested behavior: point at UI items; left click selects/confirms; right click cancels/backs out. Original game supports keyboard/controller only. No mouse feature has been installed or marked supported.

## Recovery / current installation
Diagnostic attempt was reported as crashing. Restored exact pre-test dinput8.dll and installed_files.json from main game REDELBE_LR/install_backups/roster_20260918_184118 and relaunched via Steam.
Restored SHA256: db845bee48b04b53a06e34dfdadf1d44b3b3ff8513098b2b28fb32bf0ac3f603.
Production source and public release unchanged. User confirmed recovery to main menu.

## Diagnostic history
Experimental source: experiments/mouse_menu. Must use build_combined.cmd, NOT build_proxy.cmd. First proxy-only attempt did not contain runtime instrumentation. Initial combined compile failed because text insertion landed in a different captionLayout assignment; corrected insertion scopes to layoutHook. Corrected combined SHA256 b6ec466fab0776b72b84fa8b6818936a700bbcb71682c415f0cc1c155fc32350.
Several restarts occurred during preparation; it is not established whether the reported crash was an actual exception or one of those restarts. No matching Application Error/WER entries were found in the last 15 minutes. Do not claim root cause established.
Saved evidence/mouse_probe_failed.log reaches title selection and title out. Trace logs layout hash, instance and animation, bounded to 4000 events. Do not deploy it again without resolving recovery and inspecting startup differences.

## Verified static findings (1.11 memory image, research RVAs only)
- String kids::placeable::screenlayout::DoPaneHitTest at RVA 0x4c96718.
- Registration references 0x8be454 / 0xa3ce87; VM wrapper RVA 0x3334460.
- Wrapper resolves layout, enumerates panes and constructs transformed geometry. It is NOT yet a callable mouse target API with a verified signature.
- kids::motor::lw::isSclPaneTappedByName at 0x42f3e40; registration 0x3311f40, wrapper 0x3376090.
- Despite its name, inspected wrapper calls a pane-name lookup and returns whether it exists. This is not evidence of working native mouse navigation.
- Pane name lookup 0x165dfa0: linked list layout+0x28; sentinel layout+0x48; node+0x10 pane; pane+0xb0 name pointer; pane+0x110 uint16 name length.
- NumberOfMouse string at 0x43aebd8 is configuration metadata, not a demonstrated enable switch.

## Read-only probe
 tools/inspect_menu_objects.py PID (run from research directory).
 Uses established memory helpers, validates main game path, reads bounded layout registry and panes. Output analysis/menu_objects.json. Found 981 layout entries. These may include loaded templates/inactive UI, so do NOT treat existence as visibility/selectability.
 Main cursor layout hash 0x6d610d56 has main_cursor/menu_cursor_l/menu_cursor_m/menu_cursor_s panes.
 Various row layouts expose PG_menu_text, menu_cursor, PG_text_menu. Need active instance, transformed bounds, enabled/visible status, and native selection action.

## Next requirements before installing mouse support
1. Confirm original loader recovery.
2. Obtain menu focus traces without destabilizing startup (consider existing Debug/log_ui_events instead of a new DLL).
3. Resolve live instance geometry and menu selection state; avoid screen-coordinate hardcoding.
4. Route edge-triggered left/right input only in supported menus, only while game is foreground, with no gameplay button injection or click-through on transitions.
5. Preserve keyboard/controller input, ignore hidden/disabled panes, handle scaling/letterboxing and cancel pending clicks on focus loss.
6. Add an opt-in INI/schema setting only once a functional implementation exists. Test main/submenus, character/Accessories/stage, pause, dialogs, and back behavior.

## Follow-up on working DLL
User confirmed main menu. Enabled existing Debug.log_ui_events=true (original INI saved analysis/mouse_menu_original.ini); restarted once with exact original DLL. User navigated Fight/Training/Options and Training entry/back successfully.
Main menu base hash 84b536e1: menu_in/menu_out, training_open/training_close. Rows f326b46d: text_on/off/default/dimmed/in/select/select_off. Cursor 6d610d56: cursor_l/m/s_in/out/loop.
Pane transform vfunc +0x1b0 resolves to 0x168ed50, returning pane+0xe0 pointer to matrix. Size at pane+0xf0 (signed 16-bit width,height); anchor at +0x10c. Main rows at world x=-836 map to UI x124 in 1920 reference coordinates; world y360 maps to y180 (center-origin coordinates).
Read-only captures show text root +0x113 alpha=0 for collapsed child rows, 255 for main rows. Flag +0x104 bit0x20 absent for some inactive rows despite alpha255. Need validate parent visibility and modal gating; don't assume all stored panes are active.
Native named-pane test alone is not enough. Main submenu descendants have indented x=-856, variable y. Raw bound hit-test must account for visible children and currently selected focus; hover can drive native directional actions until focus matches, then confirm with an edge pulse. Must not synthesize a disconnected controller.

## First functional prototype, pending user test
Installed SHA256 28b42b7e43b124194d56c404025c335d97f2267d8e5b7ed8c9f9d44f98126f7a; rollback checkpoint roster_20260918_185419. Isolated source experiments/mouse_menu/mouse_menu.h. Combined build passes. Public release and production sources unchanged.
Uses native row transforms, root alpha at +0x113, visibility flag +0x104 bit0x20, text_dimmed/default eligibility, centered 1920x1080 mapping. Main menu gate 84b536e1 menu_in/out. text_on records focus instance. Hover advances native direction until focus matches, left confirms then, right backs out. Input pulses65ms/spacing180ms. Foreground PID/client bounds checked.
Controller index0 must be connected; no virtual disconnected controller. Keyboard fallback Enter/Escape/arrows unverified; user says keyboard is inactive while controller is primary. Other screens are unsupported.
Read-only real-data hit-test validation retained exactly main rows [0,1,2,7,12,17,18,19,20], excluded collapsed descendants. Test requested for hover plus left/right on Training/Fight.
Before release: verify behavior, add INI enable flag, modal gating, other screen support, active controller selection, keyboard mappings and aspect ratio validation.

## Faster hover revision — 19:01
User confirmed first prototype works but dislikes visible D-pad traversal. New experimental build a3c78ec34e6b16c448fb86a0eaf3950457601710ebb9257d22f0fa5248990f75 installed with checkpoint roster_20260918_190120 (previous working mouse DLL). Direction pulses reduced from65/180ms to18/36ms. Intermediate cursor in/loop and text_on visuals suppressed; native focused ID still updated; final target animation allowed. Interrupted traversal restores real focus visuals. Crossing blank space retains last valid hovered target.
This still uses native directional input internally; it is NOT a discovered direct native focus setter. Do not describe it as instantaneous arbitrary native selection. User test requested: Story to Online skipping intermediate highlights, confirm/back. Source tests test_mouse_skip.cpp passed (intermediate suppression, final target, interruption restoration, inactive passthrough). Public release unchanged.

## 2026-09-18 Options / Sound Settings and startup click test
- User supplied Options -> Sound Settings navigation trace. Identified Options row family a37fad03 and settings rows 63d7b7fc, with PG_end_menu_text hit pane and setting_arrow_l/r controls.
- Experimental mouse_menu.h now tracks those row families, uses native pane coordinates, queues left/right input for settings arrow clicks, and accepts foreground left-click as confirm during startup/title.
- Combined build and intermediate-highlight unit test completed successfully. Installed SHA256 8b494172ea7afedd35e60ad61c0ebfd54a4f57a4f6667a1886f54431c167df08.
- Rollback checkpoint: main game REDELBE_LR/install_backups/roster_20260918_191424 (previous user-confirmed main-menu build).
- Restarted main copy; PID 36236 responding; loader initialization succeeded. Awaiting user verification of startup, Options hover, Sound Settings arrows, and back. Public release unchanged; other menu families remain unverified.

## 2026-09-18 Dialog and additional list layouts
User confirmed startup, Options and sound mouse support works. Reported exit dialog loses mouse input and requested more menus.
Read-only singleton-layout inspection added tools/inspect_dialog_objects.py (manager+0x38 hash list; existing multi-instance tree remains manager+0x70). Exit dialog 8d9b36bc has two plate hit areas at y=-104, left [-520,0], right [0,520], height60. Selected plate alpha distinguishes current choice. Runtime uses named pane geometry, not these fixed coordinates.
Experimental handler isolates dialog from background focus, supports horizontal hover/click plus right-click B, and restores prior active state on out. Tests cover active-menu restoration and preserving inactive gameplay state. Added bounded native row families for more list screens; actual screen behavior still requires live verification. Root transform scale now applied. Controller input cancels pending mouse pulses.
Test and combined compilation succeeded. Installed SHA256 7a6332a5e182d22a7933a67822e10b640d05fdf1696f66b40095e9f070649716. Rollback roster_20260918_192339 contains user-confirmed Options build. Public release unchanged.

## 2026-09-18 Versus route test (19:35)
User confirmed dialog fix. Requested Fight > Versus > Controller Side > Fight Settings > Character Select > Stage Select, and specifically costume/Accessories arrows.
Captured side singleton 1b8aa1c4 and controller panels; side_on_p1/p2 vs side_default (neutral). Fight Settings shares 63d7b7fc. Character portraits f403bcba have centers 90px apart horizontally and162 vertically despite128x256 bounds, so overlapping hit areas choose closest center. Accessories e825f3e2 uses cursor_in_p1 rather than text_on; bind its four instances and native arrow panes. Costume b384f573 provides cos_cursor_p1/p2 and cos_arrow_up/down_p1/p2. Stage base d0805c2d stage_sele_base_in/out and af1d7ac5 eleven recycled thumbnail instances: use icon_stage_1 geometry and queue relative moves from largest (selected) thumbnail, not a persistent slot identity.
Fixed old Settings hover leaking native directional input into costumes/Accessories/stages. Explicit screen transitions cancel queued input; generic navigation now expires after2seconds. Tests cover side/character/costume state and prior dialog behavior; compiled combined DLL successfully.
Installed SHA25676baf7ab463d1d3e070a18085b163dcca0701a32ee0e255be83135dffe5650c0. Rollback roster_20260918_193542. Awaiting end-to-end user test, not release verified. Current limitation: mouse injects through connected XInput index0 (keyboard fallback when no pad polling), not all possible active controller indices. Public release unchanged.
Captures: analysis/side_singletons.json, side_instances.json, character_mouse_instances.json, accessories_mouse_instances.json (latter already transitioning away), stage_mouse_instances.json. Experimental source only.

## DOA Central test — 2026-09-20
Captured layout 5228be3c instances 0–5, menu_l_on/menu_m_on and cursor_loop/cursor_off events; base d6bfa658 menu_in. Added native panel hit areas and cursor_loop focus/return tracking to experiments/aura/native_test/mouse_menu.h. Build passed; installed main game. User verification pending. Backup: backups/before_central_mouse_20260920_012729. Child screens not yet verified. No mode availability changes.


DOA Central correction: stop choosing menu_l/menu_m from alpha during cursor_loop because entrance animation has not finished. Track menu_l_on/menu_m_on per instance instead and rebind all observed panels. Compiles; installed; user validation pending.


Custom Slot first test: native layout 1235949d, cursor_slot_in/loop/sel read from doa_closet_slot_cursor.kscl. Binds visible icon_cos panels 0–9, nearest-center hit detection, horizontal selection, A/B. Disables on entry into detail controls; those controls are not yet supported. Compile passed. Awaiting runtime/user verification. Previous DOA Central build confirmed working.


Custom detail mouse test: f30929e8 active_info/select_cos/select_hair/select_glass/select_shogo restore detail focus. Cursor layout instances 10 costume, 11 arrange, 12 hair, 13 glasses, 14/15 titles. Uses native base panel bounds and alpha filtering (verified current main screen: regular panels255, arrange0). Detail screens use distinct screen6 state; native out hands off to existing costume/hair/title list handlers. Build passed; installed; user verification pending.


User confirmed custom detail mouse works. Added wheel up/down native D-pad pulses for screen6 and costume/hair/glasses/title list families 7454be7b,8f2023d0,534d6e7c. Shares existing WM_MOUSEWHEEL capture, accumulates partial detents, queue bounded8, resets on context/focus/controller/click changes. Build passed and installed; wheel runtime test pending.


# F5 battle HUD toggle — confirmed working build

2026-09-18 DLL SHA256: c3d1d7992166ddfae06f59f9281bf4f8f06f4a0ac23594c19ee5dc7e7980e8ad.
Rollback checkpoint: main REDELBE_LR/install_backups/roster_20260918_135927.

Option: UI.enable_hide_battle_hud=true, supported in metadata; user-confirmed working. F5 DIK code 0x3f is edge-detected independently of Layer2 keyboard controls and consumed only while enabled. Disabled passes the original key through. No new executable patterns or hardcoded game addresses are introduced; existing validated keyboard and layout-show/hide hooks are reused.

Original dinput8 exports SetupLSL/SetupLHL point to the hooked native show/hide routines. Original layout_show_layout_patched suppresses shows for a 22-hash set when hidden; original layout_hide_layout_patched forwards hides. Original static initialization at DLL RVA 0x125b00 constructs that set from the 22 integers at 0x13e8c0..0x13e918. Names were independently matched using LR Name2Hash database names stripped of Layout_ prefix and extensions. Inventory and names: evidence/battle_hud_original_layouts.json and battle_hud_names.json.

LR version reuses the 22 groups for battle, training, tutorials, replay/photo and shared scroll/marker UI. It additionally tracks native hide requests to avoid resurrecting groups the game has deliberately hidden. Manager binding clears obsolete requested-state entries when the manager changes. Actual native show/hide functions safely ignore absent groups; show calls while hidden are suppressed, and relevant animations reassert hidden state.

Tests: F5 rising edge/hold, disabled input, layout scope, native hide preservation and manager reset passed. Roster and INI parser tests pass; build successful. Main startup confirms all existing hooks including the confirmed break-blow patch. User was asked to test health bars, timer and training overlays hiding/restoring in offline Training/Versus. User subsequently confirmed that the F5 HUD toggle works.

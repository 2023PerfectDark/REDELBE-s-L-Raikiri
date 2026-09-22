# REDELBE LR AI versus AI prototype

2026-09-18: User confirmed the full Versus mouse route, then requested the supplied DOA6LR_Normal_Reward_Trace_v4.CT AI functionality integrated into the loader, activated by confirming a middle controller on side selection.

## Implementation
- Experimental sources: experiments/mouse_menu/ai_versus_state.h and ai_versus_hook.h, integrated into loader.cpp and mouse_menu.h.
- CPU snapshot signature copied as evidence from the table: 48 8B 00 48 8B 40 08 0F B6 14 B0 EB 02 33 D2 42 88 94 35 BE 00 00 00. Exactly one executable-section match required. Hook offset15; displaced8-byte store replayed. Live Ver1.11 site RVA0x37d911c (58560796).
- Relay preserves RAX and flags; changes DL to1 only when armed and ESI <=1. Original [RBP+R14+0xBE] store remains. No CE dependency, game files or reward patches imported.
- Existing native main menu focus instance3 is the captured Fight/Versus child. Only that route can arm middle confirmation. Main menu entry clears the route and CPU flag.
- User confirmed neutral Confirm is rejected by the original game. Prototype accepts it, sends one native left-side assignment then Confirm, with a2-second timeout. CPU override persists through the match/rematch until returning to main menu or side selection. Visual middle-to-left movement can briefly be seen during the ordinary setup route; no custom AI caption yet.
- Center mouse pane: d01a2042 instance0 PG_controller_center_off_p1. Clicking/hovering center from a side moves to neutral; confirming neutral arms AI. Controller/keyboard Confirm follows same state machine. Existing input path primarily targets XInput index0; keyboard fallback remains dependent on game primary input mode.
- CPU feature skips installation on nonunique/missing signature. No speculative course, reward, difficulty or online changes.

## Validation / installation
State tests pass: main-menu and modal mouse behavior, Versus screen transitions, AI neutral -> left -> confirm pulses, normal route reset. Combined DLL built successfully.
Installed SHA256 db2e37c68e0d032fa28c1b2f9b7c2fa75cddddb230386ea76d670bf34d559c86.
Rollback main game REDELBE_LR/install_backups/roster_20260918_194927 contains previous user-confirmed Versus mouse build.
PID8480 responding and log says AI VS AI CPU hook ready RVA=58560796.
User test requested: middle Confirm, select characters/stage, verify both fighters automatic with CE table disabled. Gameplay confirmation pending. Public release remains unchanged.

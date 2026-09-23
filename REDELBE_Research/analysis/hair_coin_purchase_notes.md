# Hair color repeat purchases (in progress)
User requests first unlock 5 tickets, reselecting a previously purchased color after switching away costs 100 native game coins. Existing local ticket unlock history must remain as purchase history, not be deleted. Existing coins confirmed by user. Default color stays free pending any contrary user instruction.

Not installed. Waiting for user to open backup Wardrobe and provide exact coin balance.
Static lr_updated.bin (newer main version, verify backup live signatures):
- string ingame_money RVA 0x4d31d48
- registration LEA RVA 0x24c19e9; accessor 0x24bdf60
- accessor invokes singleton getter 0x37d4380 then passes returned pointer to serialization function 0x24c7f30
- getter global pointer RVA 0x81a2918 (instruction 0x37d43b5 +7 +0x49ce55c)
Need verify balance representation, native spending and save path; do not write guessed currency addresses.

Live backup verified 2026-09-23: PID 15060 module base 0x7ff638860000; singleton global RVA 0x81fe928 -> 0x27ad7782130. First uint32=8287 matches user coin balance; second=14287 accumulated. Backup getter RVA 0x37f3240. Native wardrobe purchase 0x37e1090 subtracts price from first uint32, unlocks native item, increments purchase counter. Do not invoke item unlock for custom colors. Need verify native autosave trigger before enabling repeat charges.
User closed game; credited LocalTickets.dat from absent/0 to 5, atomically. Grant COMPLETE; do not grant twice. User now wants repeat cost 100 coins, NOT 10,000.

2026-09-23 test build installed and launched in backup. native_coins.h resolves singleton and scene::request_save_system_data by registrations; exact addresses verified against both lr_baseline and lr_updated dumps using test_native_coins.cmd. Save request function RVA 0x227f430, owner global 0x5e5c958 (backup) /0x5dfffa8(main). Native purchases mutate first uint32 directly; custom debit does same, then requests save. No other item unlocked.
Ticket first purchase saves color then ledger; repeat purchase checks >=100, saves color, debits100 and queues native save. Denial restores prior color INI key. Default and already-current selection free. Grid shows 100 coins for previously bought inactive colors. Existing gated setting controls charging. 5-ticket grant NOT repeated.
Previous DLL analysis/pre_hair_coin_dinput8.dll. Public ZIP not refreshed for this feature pending test. User asked to buy Black for5, returnDefault, rebuyBlack100, then restart and verify8287->8187 and savedBlack. Tests native resolver both builds and existing ticket wallet passed. Live purchase persistence not yet confirmed.

Native UI refresh verified in log: layout 0x3207f23e, text index 0/type22, matched money_in event; balance refreshed7987 then7887 after100 charge. Counter now built to animate for350ms using pumpHairColor, exact target, cancels onmoney_out. Build succeeded, pending user closes backup to install. Source layer2_runtime.h coinui namespace. No wallet orcoin grants duringthischange.

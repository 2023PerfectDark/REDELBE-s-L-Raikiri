# Development checkpoint — 2026-09-23

## Confirmed in the backup game
- 5-ticket first hair-color purchase; 100 native-coin repeat selection.
- Native system-save request after coin deduction.
- Wardrobe counter refresh and 350 ms countdown; user confirmed countdown works.
- CRLF wallet fix. A one-time user-requested 5-ticket grant is complete; do not repeat it.
- Generated hair-resource index alignment fix restores startup.

## Built, still needs game verification
- 1 GiB on-demand hair-color cache (real-resource/frozen worker and eviction tests passed).
- Full-palette random CPU colors for offline Versus, including AI vs AI.
- Coin persistence after a full restart should still be explicitly confirmed.

## Backup/release status
Source backup includes the latest installed countdown code. The public Alpha 152 ZIP
has not yet been refreshed with the ticket/coin/countdown changes; its changelog and
source are updated. No game assets, personal wallet/save files, generated palettes,
or compiled release binaries are included in the source backup.

Build: experiments/hair_color/native_test/build_combined.cmd.
Checks: test_ticket_wallet.cmd (including CRLF); test_native_coins.cmd resolves both
local game versions; tools/test_hair_cache.py and test_hair_cache_frozen.py.
The native resolver test requires locally supplied binary research images, which
are intentionally not in Git. Installed target: backup game, not the main game.

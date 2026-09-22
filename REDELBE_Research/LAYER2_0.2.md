# REDELBE LR prototype 0.2 — Layer2 controls

## Installed copy

`G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415`

Launch using Steam's Play button with the existing test-launcher setting.
The original installation was not modified by this update.

## Controls

Character costume selection now displays `Slot: AYA_COS_001 Mod: Vanilla`,
updating to the selected Layer2 mod's name when cycling. Labels use the native
caption pane. 623 costume names are mapped from the local LR name database;
unmapped slots display their hexadecimal hash. User confirmed the display works.

The current build includes the Kashira bridge; see `KASHIRA_WORKFLOW.md`.
User confirmed character select and cycling after the bridge installation.
Installed ASI SHA256: `7fc5adedab70fce68bd46e1cfa32a15d8fc9b7f139c8aa454a315d70114f5160`.
The native Kashira correction adds Minato, Momiji and Rachel for 24 Layer2 mods;
635 caption names now include Minato. User confirmed Minato switches between
Vanilla and Liza Dress in both directions. Details: `KASHIRA_WORKFLOW.md`.

On a character's costume-selection screen:

| Input | Action |
|---|---|
| F | Next Layer2 mod |
| L2 on PlayStation / LT on Xbox | Next Layer2 mod |
| Select / Back | Previous Layer2 mod |

Every list includes **Default**, the normal costume. At startup all slots and
players start on Default. The installed collection has **21 Ayane mods**:
6 on `AYA_COS_001` (including Ayane Test) and 15 on `AYA_COS_105`.
See [the full list](AYANE_21_MODS.md). F/LT cycles through the selected slot's
mods and wraps back to Default; Back cycles in reverse.
Selections are remembered per player and costume during the current game session.

Manual cycling now releases the selected player's body request through the
game's native clear routine, lets cleanup run for 300 ms without blocking the
game, then requests the preview with all four cache checks bypassed. This fixes
the earlier behavior where makeup refreshed but the outfit stayed cached until
the user changed costume slots. The user confirmed outfits now change correctly
without leaving the slot. All 27 captured cycles reopened the body model file.
The game manages the remaining loading time and visibility; no fixed three-second
pause is imposed. Natural costume navigation cancels a pending manual reload.

Only catalog metadata and resource mappings are read at startup. Replacement
models/textures are opened when the selected mod's resources are requested.
Unselected mods' payloads are not preloaded. Switching back to Default routes
subsequent requests to the original assets; the game controls its own memory caches.

## Random character selection

An experimental hook is installed for the game's Random character selection in
**offline Versus and Free Training**. After the game selects a costume, the loader
chooses Default or one of the mods registered for that costume. Other costumes
remain unmodified. No asset is opened merely to make the random choice.

The user confirmed a match loaded with the first random update. Its log exposed
future-result prefetching, so the current build queues random choices and waits
for a matching character-load call before activating one. The user now confirms
Random works. The live Versus log records Ayane Xmas 2019 XNALara-XPS queued
and activated for P1 on AYA_COS_001 at the matching character load, followed by
replacement asset opens. This validates a real modded result with the queue correction.
Free Training uses a separate caller and has not been separately confirmed.
Arcade/Survival random opponent preloading is not enabled: those modes need
separate handling for future opponents. The prototype does not add a new Random
costume entry to the menu.

The log records `LAYER2 RANDOM EVENT`, then `LAYER2 RANDOM QUEUED` for supported
callers, `LAYER2 RANDOM ACTIVATE` at a matching load, and `LAYER2 OPEN` if the chosen mod's resources are read. A default random
choice or a costume without registered mods should not produce mod-file opens.

## Adding mods

The prototype uses **prepared LR hash-named assets**, stored under
`REDELBE_LR\Layer2`. It does not yet load arbitrary original DOA6 REDELBE folders
or convert their models automatically. A `mod.ini` alone is not enough: its
resource tables, original-asset fallback, and shadow index must be prepared.
The 20 new entries are experimental local DOA6 ports using the resource mapping
method found in the working LR Attitude Dress package. Model/texture versions
match; legacy textures absent from LR's index are omitted and recorded in
`analysis/ayane_twenty_import.json`. Visual compatibility is not yet verified.

From the research directory, prepare a new empty output directory using:

```powershell
python tools/build_layer2_package.py packages/my_layer2 `
  --game 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415' `
  --mod AYA_COS_001 'First mod' 'C:\path\to\first\assets' `
  --mod AYA_COS_001 'Second mod' 'C:\path\to\second\assets'
python tools/verify_layer2_package.py packages/my_layer2
```

Repeat `--mod` for every desired mod; the generated catalog's order is the cycle
order within a costume. Include the complete desired set when rebuilding.
Asset names must use LR resource hashes, such as `0x63438245.g1m`.
Close the game, then install using `tools/deploy_probe.ps1` with explicit
`-GamePath` pointing to the copied installation and `-PackagePath` to the new package.

There is no 500-entry limit. Automated selection tests traverse 500 entries in
both directions and wrap through Default. This is a state-logic test, not a
500-real-mod memory/performance benchmark.

## Validation and limits

- User confirmed F, Select/Back, and L2/LT visually switch normal/modded Ayane.
- Saved control log contains all three inputs, original and replacement reads,
  and no mod payload open before the first manual selection.
- The expanded package and installed copy both passed verification of all 483
  replacement payloads, 93 original fallbacks, and the 21-entry catalog.
- The current update starts and passes executable/archive/hook signature checks.
- User confirmed Random works; the saved log corroborates mod activation in Versus.
- Free Training random behavior, two-player resource conflicts, and extended match
  stability still require testing. Slot/mod-name display is installed for visual validation.

## Checkpoint

Confirmed controls build:
`backups/layer2_controls_confirmed/REDELBE_LR.asi`

SHA-256: `41c191281d076654a18a46961a24d4e4682eeb09e2ea39383bb8685f56afde79`

Random test update:
`prototype/build/REDELBE_LR.asi`

SHA-256 (current caption update):
`347a8e5427501e1a8f2c45d47cf4e0017a1ee098a395bc036b4608904e5e5649`

Confirmed body-release build:
`f466ca07f43c081a418658ddcd4e149a336ba1570cc32414ed72b80428d12211`.
Full backup before caption update: `backups/20260916_000620_196`.

Confirmed build and matching source: `backups/layer2_body_reload_confirmed`.
Evidence: `evidence/layer2_body_release_test.log` and
`evidence/layer2_body_release_reads.json`. The user closed the game voluntarily
after successful testing; the exit was not reported as a crash.

The confirmed Random build is saved in `backups/layer2_random_confirmed`:
`247f6de8c3e0a1730fe13c238e8f6fbec8edcd933cfc53890555f41c8a8f7c97`.
The full installation before the preview-reload update is saved in
`backups/20260915_232350_935`.

The full previous installation is saved under `backups/20260915_221651_253`.
The one-mod installation immediately before adding 20 mods is saved under
`backups/20260915_225609_627`.
To revert just the random test update, close the game and restore the confirmed
ASI into the copied game folder. Keep the existing Layer2 data package.

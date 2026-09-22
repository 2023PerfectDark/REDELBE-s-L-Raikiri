# REDELBE LR + Kashira

Installed on September 16, 2026 in:

`G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415`

## Latest preparation fixes

The installed sync helper checks the executable path of actual DOA6LR processes.
It no longer mistakes a reader holding the EXE open for a running game. A real
running backup copy still blocks synchronization and reports its process ID.

Binary OID/MTL reference tables are validated against their registered LR
resource types instead of comparing their first four bytes with Vanilla. MTL
record boundaries are also validated. This fixes preparation of Tina's Patriot
Bikini package, whose table contents differ from the original costume.

The current installed collection has 29 prepared Layer2 mods (634 payloads,
215 Vanilla fallbacks). The five additions are Tina TIN_COS_105, Kasumi
KAS_COS_105, Tamaki SKD_COS_105, Mila MIL_COS_103 and another Ayane AYA_COS_105
mod. Preparation and payload verification succeeded; their appearance in-game
has not yet been individually verified. The 24-mod checks below describe the
previous collection and its confirmed Minato test.

## Editing the prepared mods

### Normal Kashira Editor costume projects

Build `.ktmod` normally in Kashira Editor. Close the game, then use the existing Steam Play setup / REDELBE launcher. It now recognizes a native costume build when its G1M resource identifies one costume slot, converts the installed package to Layer2, and rebuilds the global base without that costume replacement. Rebuilding the same project later is supported: conversion runs again on the new package.

The original project can keep its normal flat `Content_Legacy` layout. The installed `.ktmod` is normalized automatically. Its original package and pre-Apply indexes/FDATA are backed up under `REDELBE_LR\kashira_backups`.

Current newly converted slots:

| Character | Slot | Mod |
|---|---|---|
| Minato | MNT_COS_011 | Last Days of Summer Liza Dress SFW |
| Momiji | MOM_COS_105 | Last Days of Summer Liza Dress SFW |
| Rachel | RAC_COS_005 | Uncensored Fiend Costume |

They start at Vanilla. F/LT selects the mod; cycling back selects Vanilla. The 21 Ayane mods remain available, for 24 total.

### Prepared Ayane projects (optional direct loose editing)

1. Open `KashiraEditor-win-x64.exe` and choose **Open Existing Project**.
2. Open `KashiraProjects\REDELBE_LR_0001\project.ktproj` in the backup game folder (Ayane Test). The other 20 projects are numbered 0002–0021.
3. Browse `Content_Legacy\REDELBE_Layer2\AYA_COS_001` (or `AYA_COS_105`). Edit the hash-named G1M/G1T files there.
4. Save your changes. Close the game before synchronizing. Launch using the existing Steam Play setup / `REDELBE_LR_Launcher.exe`. The launcher prepares changed files before starting the game.

For registered projects, saved payload edits newer than the installed package are read directly. A newer built package takes priority over an older loose project. **Build .ktmod is optional for testing loose edits to these registered projects**. Keep the project name unchanged when updating an existing package: it matches the installed package filename. The shorter in-game name is stored in `Content_Legacy\redelbe_layer2.json`.

Kashira's DOA6LR library entry now points to the backup installation, so Editor Build and Manager Apply use that copy. This is a shared Kashira preference, also visible to other copies of Kashira. Its previous setting is backed up with the working loader checkpoint.

## Selecting available mods

Open `Kashira-win-x64.exe` and use the DOA6LR entry pointing to the backup installation. The 21 Ayane packages begin with **REDELBE LR - 0001**, etc. The three converted native costumes retain their existing package names.

- Kashira's Default profile enables all installed packages. Create/select a custom profile to disable individual mods or change their order.
- Enabled Layer2 packages are available to F/LT/Back and Random. Every costume still starts at Vanilla.
- F / L2-LT cycles forward; Select-Back cycles backward, including Vanilla.
- Manager Apply continues to handle ordinary global Kashira mods. After Apply finishes, launch through the REDELBE launcher so its overlay is rebuilt against those indexes.
- `Sync REDELBE Layer2.cmd` runs preparation manually and shows errors. Directly launching DOA6LR.exe does not run synchronization.

The marker and nested asset directory keep converted packages out of Kashira's global replacement list. Manager may show **0 file(s)**: that is its global file count, not the Layer2 payload count. `REDELBE_LR\bridge_sources.json` lists which package/project each Layer2 mod uses. `kashira_prepare.log` records automatic conversion and global-base preparation.

## Other projects and file formats

The adapter recognizes native G1M costume builds with one identifiable costume slot. Texture-only mods, animations, backgrounds, and effects cannot automatically be assigned to a costume this way and retain their normal global behavior. Ambiguous G1M costume mappings stop preparation with an error instead of guessing. Explicit marked Layer2 projects remain supported.

To author another Layer2 package, copy a prepared project, assign a new UUID in `redelbe_layer2.json`, set its costume slot and in-game name, and give its `.ktproj` a unique Name. Preserve the nested asset layout. Editor Build installs the new package; the bridge reads its packaged assets on the next launch. To use saved loose edits directly, add its package stem and game-relative project path to `REDELBE_LR\bridge.json`.

Editor can display arbitrary files, but runtime preparation currently requires existing LR resource IDs, hash-named files, and matching native payload types. Visibility in Content_Legacy does not convert incompatible DOA6 files, DDS files, or new unregistered resource IDs into usable LR assets.

## Verified

- Kashira's own package reader accepted 21 packages with no global replacement entries.
- Kashira's editor code enumerated all 483 assets and its actual Build method preserved the marker and nested files.
- Current generation verification checked 522 mod payloads and 130 original fallback payloads across 24 mods.
- Minato, Momiji and Rachel model fallbacks match the pristine Kashira backup assets and differ from their selectable mod models.
- The native adapter reapplied 52 ordinary global assets, removing the three costume packages from the always-on base. Pre-change indexes, generated FDATA and original packages were backed up first.
- Momiji contains unused texture ID `0xafbec60c`, absent from LR's resource index. It is retained in the package but skipped during preparation, matching Kashira's legacy behavior.
- Profile ordering/disable behavior, package roundtrip, duplicate IDs and path validation tests pass.
- ASI attachment on a 16 KB thread stack passes after fixing a startup crash found during testing.
- User confirmed Minato's MNT_COS_011 switches to Liza Dress and back to Vanilla. The live log also verifies it starts on Vanilla and opens the corresponding original/mod models. Momiji and Rachel have asset-level fallback verification, with their individual visual checks still pending.
- The launcher prevents overlapping launches and shows the saved specific preparation failure from `REDELBE_LR\bridge_last_error.txt` instead of only a generic error.
- REDELBE rejects attachment in Kashira Editor/Manager, avoiding game-hook initialization and DLL locks in those tools.

The installed application's project-picker automation did not reliably accept input; UI opening/building a project was not independently confirmed. Package/editor code compatibility and in-game operation were verified as described above.

## Rollback

The native-conversion update changes the backup game's global base. Its pre-change indexes, generated FDATA, patch record and three original packages are in the backup game's `REDELBE_LR\kashira_backups\20260916_012345_443`. To return to the pre-conversion global setup, restore those original packages into `_Kashira\Mods`, its indexes/FDATA into `fdata_package`, and its `rdbpatch.json` into `_Kashira`, with the game closed. Restore the older sync executable from research `backups\native_kashira_before_20260916_012343` to stop automatic native conversion. Preserve subsequent user edits before restoring older files.

Close the game. The pre-bridge working loader, launcher, entire REDELBE_LR folder, caption source, and previous Kashira library settings are in:

`REDELBE_Research\backups\kashira_before_20260916_003802`

Restore its `REDELBE_LR.asi` and `REDELBE_LR_Launcher.exe` into the backup game folder. The previous loader ignores `active_package.txt` and uses the original flat package, which remains intact. Restore `games.json` to `%APPDATA%\Kashira\games.json` only if you want Kashira linked to the original installation again.

Prepared generations under `REDELBE_LR\sets` are retained for recovery and consume disk space after edits. Do not delete the generation named by `active_package.txt`. Projects and packages are separate from these generated files.

## Private textures: groundwork only

`analysis\texture_audit\texture-sharing.json` maps 745 costume material chains from Kashira's pristine backup indexes. It found 940 texture IDs shared across character prefixes. This covers MI/MRNH chains; it is not a complete face/hair/all-resource dependency audit.

`analysis\texture_audit\private_tina_proof` contains an uninstalled structural proof: shared texture `0xcc3625e2` is copied to new ID `0x0fa00000`, with a cloned Tina material chain. All 196,945 original material records remain unchanged. The serialized new material was parsed and verified.

**Character texture isolation is not active yet.** Remaining work: repoint only the intended costume, register private resources against current live Kashira indexes, map Layer2 replacements to private IDs, and test two characters together. Two players using the same costume with different mods also need separate validation.

Integration contract and material-chain research use the official Kashira source: https://github.com/umin135/KashiraModManager

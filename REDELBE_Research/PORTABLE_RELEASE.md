# REDELBE LR 0.3 release candidate

## Compatibility design

The loader resolves complete x64 functions from the runtime PE function table.
Patterns mask external relative calls and RIP-relative addresses, retain internal
branch offsets and structure-field offsets, require a unique match, and verify the
model initializer/cache/scale call graph and the two supported random-selection callers.
The body-release helper has three identical implementations; it is selected from
the verified request function's call target, then checked against its own pattern.
XInputGetState is found by import name. No executable checksum whitelist is used.

This handles relocation, not arbitrary future code or layout changes. Missing or
ambiguous matches reject initialization before game hooks are written. An update
that changes a complete function may require new reviewed patterns.

## Evidence

- The C++ resolver passes the original runtime and Ver. 1.11 runtime.
- Negative tests reject a modified initializer and duplicate matching entries.
- Ver. 1.11 random function moves from 3919430 to 38fa570; load function moves
  from 2a3f740 to 2a3f830. Both supported random callers move as well.
- Model-default, scale and cache functions still match the original implementation.
- The earlier `game_update_audit.json` on-disk hook comparisons were inconclusive:
  executable code is protected on disk. Use runtime-pattern evidence instead.
- Four bridge regressions pass; three installer/remover regressions pass.
- Packaged EXE install/self-removal passes in an unrelated folder with spaces.
- Main Ver. 1.11 preparation: three Layer2 packages, 39 assets, 38 Vanilla fallbacks;
  52 ordinary Kashira assets applied. Actual installed Kashira.Core is used.
- The initial two-DLL startup design exited early. Consolidating loader and proxy
  into one dinput8.dll fixed standalone startup. User confirmed Minato cycling on
  Ver. 1.11 first with the older bootstrap, then with the standalone single DLL.

## Portable runtime

The release contains an original combined DirectInput proxy/loader, launcher, standalone sync
tool, standalone .NET helper/runtime, notices, and install/remove scripts. It contains
no user mods, game resources, captured runtime images, personal logs or Kashira.Core.
Kashira.Core is read from the user's installed Kashira manager at preparation time.
The adapter is built against that supplied version's API, not a redistributed fork.

Kashira index baselines are refreshed before reading costume data after an update.
The adapter exports current costume slot names rather than relying only on the old
compiled name table. Projects may use relative paths; ordinary single-slot legacy
costumes are converted from Editor builds. Ambiguous packages and authored material
manifests need explicit preparation; this is not automatic conversion of every mod.

Removal preserves mods/projects and moves matching runtime files and generated data
into a dated removed folder. Unchanged automatically converted packages are restored
from the conversion journal. Modified files are preserved, not deleted.

## Distribution status

RC2 standalone startup and Minato in-game controls are user-confirmed. Other-PC
coverage and a Ver. 1.11 randomization regression test remain unverified. The
working backup game was not upgraded during this task. Main-game install/preparation
checkpoints are under its REDELBE_LR folder. Do not distribute intermediate diagnostic
packages as a verified release. Use packages/REDELBE_LR_0.3_RC2.zip for wider testing.

Final RC2 installed in the updated main game; pre-existing winmm.dll restored.
Final sync reports unchanged / three mods. Root REDELBE_LR.asi is absent, preventing
double initialization; the old ASIs are preserved inside the REDELBE_LR test/checkpoint
folders. The working backup installation remains unchanged.

ZIP SHA256: 6dc8be1b3b6dc2be9fc36bf752cfd8bfabedea3684e740463cd776bb4e488524

Installed dinput8.dll SHA256: e41e098bfb12972a242ea82ada86db5d2d7d699b8bde2f4625fcf3f16db4dc80

## RC3 title branding (2026-09-17)
Installed in main game; user confirmed the full Ver. 1.11 / Raikiri 0.3 RC3 label is correctly positioned. Native title text hook pattern matches both captured versions. Editable UTF-8 REDELBE_LR/branding.ini is created only if missing, preserved on upgrades; restart after edits. Temporary text tracing removed. Package: packages/REDELBE_LR_0.3_RC3.zip. Previous RC2 DLL preserved in main REDELBE_LR/install_backups/branding_rc2. Other-PC testing remains outstanding.

## RC4 hair/head Layer2 (2026-09-17)
Separate hair/head and costume selections; F/LT forward and Back backward in the hair/details menu. Caption shows HAIR slot and selected mod. Kashira preparation accepts COS/HAIR/FACE markers and exports all slot names. Main game contains two test projects in addition to the three existing costume packages. Eve ponytail cycling/caption user-confirmed; Hanabi visual confirmation pending. Selection and bridge tests pass. Package excludes example assets.
ZIP SHA256: 434e6869b5de32296c9cc60b07149257bb491b39cc24577b82c07d32b3d78711
Details: HAIR_LAYER2.md.

Final RC4 confirmation: user reports Eve caption and hair cycling work, and Hanabi hair, face textures, and Vanilla all work. Installed main-game build and public package match. Full details in HAIR_LAYER2.md.

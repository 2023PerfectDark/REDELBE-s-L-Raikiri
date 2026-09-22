# REDELBE → Dead or Alive 6 Last Round investigation

**Current status:** See `LAYER2_0.2.md`. F / Select-Back / L2-LT cycling is now
implemented and user-confirmed, with Default at startup. The new offline
Versus/Free Training Random-character hook is installed for a live match test.
The 0.1 investigation and reproduction commands below are historical.

## Result, September 15, 2026

### Later test-copy follow-up

The user confirmed visible Ayane costume replacement in character selection.
The copied installation now runs through `REDELBE_LR_Launcher.exe` using Steam's
launch option. This fixes both Steam relaunching the original EXE and a direct
EXE override retaining the original working directory. Runtime verification
confirmed the copied executable, copied working directory, shadow index redirect,
and requests for the Ayane model plus 49 other replacement assets. See
`TEST_COPY_LAUNCH.md` and `evidence/test_copy_launcher.json`. The test copy remains
installed. Full Layer2 and match stability are still unfinished. The earlier
investigation record below describes the initial title-screen-only test.

**A Last Round startup and resource-index overlay prototype was built and tested.
Full REDELBE compatibility is not complete.**

The experimental ASI reached the Last Round 1.10 title screen with a shadow
`root.rdb` enabled. Its log records redirection of the game's resource-open request
to that shadow index. A 56-asset Ayane replacement package was prepared and passed offline
round-trip checks. The costume itself was **not verified in game**: automated
keyboard input did not advance the title prompt. No selection, hair cycling,
stage, match, or Layer2 validation is claimed.

The test loader and overlay are removed from the game at the end of the test.
The source, binaries, package, logs, and backups remain in this research folder.
See `STATUS.md` in the workspace for final installation state.

## Verified inputs

| Input | SHA-256 |
|---|---|
| Original `DOA6.exe` | `7922bba920bf471730baad946b2641553f6957f510a5eaca39ea6ce9634b1efc` |
| Target `DOA6LR.exe` | `35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea` |
| Supplied `dinput8.dll` | `4bbcc44a4b11260936882f4ec7b32084e79a21d48d1d8ab26bda1a4bae571337` |
| Prototype ASI tested at title screen | `5c173a1a0593766a9e07187d144ec6f0fdd2f6522f6b53d1bff5dc3ca7dc8c71` |

The supplied DLL matches the original game's installed REDELBE DLL. The target
Steam manifest identifies app **4144680**, build **25053795**. The executable's
version resource says 1.0.0.0, while the actual title screen says **1.10**.

## Source correspondence and reproducibility

- [REDELBE source](https://github.com/eterniti/redelbe), commit
  `54a12131933e3a595ce738d7a1135413ed6aea1f`, is checked out in `source/`.
- [eternity_common](https://github.com/eterniti/eternity_common), commit
  `252d52b1d77d2bafe918ecdb143530b54e7edb31`, is in `eternity_common/`.
- Six of seven public XML patch files exactly match the supplied archive.
  `misc.xml` differs. Public `redelbe.h` labels itself 3.1; the supplied archive is
  the user's 3.0 package. This is strong correspondence, **not** a reproducible
  binary match.
- The public build needs MinGW64, MinHook, zlib, and the common library. Seven
  included `DOA6/hashes/additional_fn_*.h` files are missing from that checkout.
  The original Makefile also copies its output into the author's game directory.
  It was inspected, not executed.
- The new prototype is an independent, small MSVC implementation of an index
  overlay, informed by the original resource/startup design. It does not compile
  or contain the original Layer2 implementation.

## How the original loader works

1. `dinput8.dll` acts as a proxy and forwards to the system DirectInput library.
2. Startup recognizes `doa6.exe` and hooks `GetStartupInfoW` to initialize later.
3. A module-enumeration compatibility hook excludes REDELBE itself; the source
   notes that the original game otherwise terminates it.
4. XML signatures find game functions and data. Enabled patch failure terminates
   startup. Several structures and assumptions are compiled into C++ as well.
5. `rdbemu.cpp` rewrites resource index entries in memory and intercepts Windows
   file APIs to present replacement data through virtual files and handles.
6. Layer2 hooks character/costume/hair/stage selection, determines active mods,
   and changes the resource view. This is substantially more than file copying.

## What changed in Last Round

### Executable and hooks

Both games import DirectInput8, but the target is `DOA6LR.exe`. Renaming a DLL or
changing the process-name check cannot supply the missing game hooks.

The earlier raw-file scan found zero matches in both games. A read-only snapshot
of the running LR executable yielded **7 matching patterns out of 67**, each
unique in executable sections. Only **3** are in `layer2.xml`:

| Pattern | Target RVA |
|---|---|
| LocateGDS | `0xE4AE99` |
| LocateLO | `0x2309DE5` |
| Transform6 | `0x3A56E54` |
| RandomMusicPatch | `0x39A26B6` |
| LocateLO2 | `0x2309DE5` |
| PatchLSL | `0x1F87FC2` |
| PatchLHL | `0x1F7B917` |

These are candidate locations, **not validated callable hooks**. Original search
ranges, settings, patch ordering, function arguments, and structure layouts have
not been ported. The other 60 full signatures did not match this runtime snapshot.

### Resource system

- `fdata_package/root.rdb`: 81,154 entries.
- `fdata_package/system.rdb`: 96,198 entries.
- RDX tables map 16-bit package IDs to hashed `.fdata` filenames.
- RDB entries contain resource IDs, payload sizes, flags, and package locations.
- This installation already contains 141 external root resources (`0xC01`),
  providing real examples of uncompressed `data/0x########.file` containers.
- The name database records point to absent `0x11eb7849.fdata` and
  `0xa9992094.fdata`. Name recovery therefore needs other evidence; the prototype
  uses explicit existing LR resource IDs.
- Existing Kashira changes are present: the installed root index differs from
  Kashira's backup. The prototype builds from the **installed** index to preserve
  those changes and checks its hash before enabling redirects.

The supplied `CharacterEditor` XML independently maps resource `0x63438245` to
`CE1ResourceModel［AYA_COS_001］`, the model used for the test package.

## Prototype design

`prototype/loader.cpp` exports `InitializeASI` for the already-installed Ultimate
ASI Loader (`winmm.dll`). It adds a separate `REDELBE_LR.asi`; existing proxy DLLs
and their settings are preserved.

- Checks the exact executable SHA-256 before installing hooks.
- Checks base RDB/RDX hashes before enabling an asset overlay.
- Hooks the main executable's `CreateFileW` import and handles `CreateFileA` when
  available; LR has one relevant CreateFile import.
- Redirects only read-only `OPEN_EXISTING` requests in `fdata_package`, using an
  immutable explicit path table. It returns real Windows file handles, so the
  game retains normal read, seek, asynchronous I/O, and mapping behavior.
- Implements the original REDELBE module-query compatibility behavior for **only
  its own module**, only for the game's query of its own process, with buffer
  bounds checks. This behavior is visible in the source and log.
- Does not hook costume selection or load old XML patches.
- Has no hot reload. Changes require a game restart.

`tools/build_overlay.py` prepares a shadow index and separate IDRK-wrapped `.file`
payloads. It preserves entry sizes and unselected entries, rejects unknown or
duplicate resource IDs and mismatched payload families, and verifies extraction
of generated resources against input hashes. It does **not** convert DOA6 assets.

## Test evidence and limits

| Check | Result |
|---|---|
| MSVC x64 build | Passed |
| Installed archive entry counts | Passed |
| Corrupt entry bounds rejected | Passed |
| Unknown replacement resource rejected | Passed |
| All 56 generated payloads extract exactly | Passed |
| Only intended RDB metadata bytes changed | Passed |
| Initial baseline title screen | Observed, LR 1.10 |
| Probe without module-query compatibility | Exited before title in direct-launch tests |
| Probe with compatibility and overlay | Title screen observed; remained running |
| Shadow index open request redirected | Logged; game reached title |
| Ayane payloads opened/rendered | **Not observed** |
| Selection, match, two players, restarts with costumes | **Not tested** |
| Original archive preservation | Hashes recorded; originals not written by project |

Some restart attempts also stalled in the baseline; one direct launch returned
53. Steam launch restored the baseline. The stalled test thread was in the
game's `GetMessageW` loop with Steam overlay frames among raw stack candidates.
Those candidates are not an unwound call stack and do not establish a root cause.

Evidence: `evidence/title_screen_overlay.png`, `evidence/overlay_startup.log`,
`evidence/archive_hashes_after_test.json`, `analysis/lr_baseline.signatures.json`,
and timestamped `backups/*/deployment.json`.

## Compatibility matrix

| Feature | State |
|---|---|
| LR 1.10 ASI startup | Demonstrated on this installation |
| Shadow index redirect | Demonstrated |
| LR-native assets named by resource ID | Package builder ready; visual test pending |
| Arbitrary original REDELBE named replacers | Unsupported |
| Original DOA6 asset conversion | Not implemented |
| Layer2 costume/hair cycling and slot redirection | Not implemented |
| Layer2 stages, music, UI patches | Not implemented |
| Other LR executable builds | Disabled by fingerprint |

## Build and reproduce

Run from this workspace in PowerShell:

```powershell
& '.\REDELBE_Research\prototype\build.cmd'
& 'C:\Users\Owner\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.\REDELBE_Research\tools\test_resources.py'
```

The build script uses the installed Visual Studio 2022 x64 toolchain and static
C++ runtime; no downloaded runtime DLL is required for the ASI. Analysis-only
dependencies are pefile 2024.8.26 and capstone 5.0.9 in `tools/python_deps`.

For a deliberate continuation test with the game closed:

```powershell
& '.\REDELBE_Research\tools\deploy_probe.ps1' -Action Install -PackagePath '.\REDELBE_Research\packages\ayane_full_test'
# Launch through Steam. Select Ayane's AYA_COS_001 slot in a local mode.
# Inspect REDELBE_LR/loader.log for data/0x63438245.file and texture redirects.
# Close the game before removal:
& '.\REDELBE_Research\tools\deploy_probe.ps1' -Action Remove
```

The removal action moves only the project's ASI and data folder into a dated
workspace backup. It does not uninstall the user's other loaders or mods.
Game-folder writes require the tool environment's approval regardless of broad
authorization in a chat prompt.

## Next engineering work

1. Complete visual and offline-match validation of the native-ID overlay.
2. Expand name mapping from the existing LR XML/resource databases and compare
   old/new asset formats; do not assume matching filenames imply compatibility.
3. Resolve Layer2 function counterparts with disassembly and runtime observations;
   validate data layouts and both player slots before installing hooks.
4. Add selection-driven resource switching and cache invalidation, then test
   costume, hair and stage transitions and repeat launches.

Additional format evidence: [Katana engine asset-system research](https://github.com/umin135/katanaDOCS/blob/main/01_katana_engine_asset_system.md).
Its claims were treated as leads; local parsing and extraction are recorded above.
# Layer2 0.2 update

The later Layer2 implementation and current validation are documented in
`LAYER2_0.2.md`. This supersedes earlier statements below that Layer2 cycling is
unimplemented. The user confirmed all three controls visually. The controls log
and verification results are in `evidence/layer2_controls_confirmed.log`,
`evidence/layer2_control_verification.json`, and
`evidence/layer2_package_verification.json`. Random character support for offline
Versus/Free Training loaded a match in the first test. A subsequent correction
queues prefetched results. The user now confirms Random works, corroborated by
the Versus log activating Ayane Xmas 2019 at the matching load and opening its
replacement files. Free Training is not separately confirmed.
The test copy now has 21 Ayane entries (20 new experimental ports), described in
`AYANE_21_MODS.md`. All 483 replacement payloads and 93 vanilla fallbacks were
verified after installation. Startup logs confirm `catalog=21` and `active=0`.

Manual preview cycling now also clears the native body request before a short
non-blocking cleanup interval and reload. The user confirmed outfits change
without leaving the costume slot; all 27 captured cycles reopened the body file.
See `backups/layer2_body_reload_confirmed` and `evidence/layer2_body_release_test.log`.

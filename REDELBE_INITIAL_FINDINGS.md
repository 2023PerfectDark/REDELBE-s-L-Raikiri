# REDELBE initial inspection — 2026-09-15

## Status

Initial read-only inspection and handoff preparation are complete. No game files were changed, no loader was installed, and neither game was launched. A compatible Last Round port has not been built or tested. The separate Kula/RE9 assets were not located or inspected during this task.

## Verified local evidence

| Item | Finding |
| --- | --- |
| Supplied archive | `C:\Users\Owner\Downloads\Compressed\redelbe_30_2.zip`, 1,072,823 bytes |
| Archive loader | `dinput8.dll`, 4,421,632 bytes |
| Loader SHA-256 | `4bbcc44a4b11260936882f4ec7b32084e79a21d48d1d8ab26bda1a4bae571337` |
| Reference loader | Byte-for-byte identical to the archive DLL |
| Reference executable | `DOA6.exe`, 44,261,008 bytes; version metadata 1.0.22.1 |
| Reference SHA-256 | `7922bba920bf471730baad946b2641553f6957f510a5eaca39ea6ce9634b1efc` |
| Target executable | `DOA6LR.exe`, 107,914,232 bytes; version metadata 1.0.0.0 |
| Target SHA-256 | `35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea` |
| PE architecture | Both executables are x64 / PE32+ |
| Loader entry opportunity | Both executables import `DINPUT8.dll`; this does not establish runtime compatibility |
| Existing target ASI loader | `winmm.dll`, version metadata Ultimate-ASI-Loader-x64 8.2.0 |
| Other target proxy | `version.dll` is already present; preserve and assess coexistence before deployment |

Game paths are recorded in the companion brief and JSON report.

The supplied ZIP includes user/modder READMEs, REDELBE.ini, seven XML patch files, resource replacement directories, Layer2, and optional sample configurations. It does not include C++ source. Its documentation describes direct replacements and Layer2 selection. The XML files contain byte signatures, old search-start addresses, hook/setup export names, and direct code edits. These are technical evidence, not user instructions to install or activate every feature.

## Source discovery

A public [REDELBE repository](https://github.com/eterniti/redelbe) contains C++ source and patch definitions. Its README names MinGW64 GCC, `eternity_common`, and MinHook as build requirements. Source correspondence to the supplied DLL and build completeness are unverified.

The inspected [main.cpp](https://raw.githubusercontent.com/eterniti/redelbe/main/main.cpp) checks the process path against a `PROCESS_NAME` constant, forwards proxy exports to the system DLL, loads XML patches, and exits on an enabled patch application failure. The constant's value was not verified here. Startup gating, initialization timing, and patch-failure behavior therefore need explicit investigation during the port.

## Static signature triage

`inspect_redelbe.py` reads the ZIP and executables without loading them. It records PE sections, import names, SHA-256 fingerprints, and scans executable sections for concatenated XML Instruction patterns with XX byte wildcards. It normalizes malformed XML attribute syntax for parsing in memory only; the ZIP is unchanged.

Result: **0 of 67 patterns matched in DOA6; 0 of 67 matched in DOA6LR.**

This is inconclusive. The scan ignores enabled settings, original scanner semantics, runtime transformations, and sequential patch effects. Both executables have a `.bind` section, but its presence alone does not establish why patterns were absent. Because the reference executable also produced no matches, these results cannot prove that Last Round is incompatible. Inspect authorized running-process code and the original scanning implementation before drawing conclusions. Do not disable checks or install old hooks based on this scan.

## Next technical step

Retrieve and inspect the source with its dependencies, establish a reproducible reference build where possible, and compare runtime initialization and resource handling against the target. Build a narrowly scoped diagnostic loader only after resolving the entry path and existing loader coexistence. Then validate file replacement before expanding Layer2 support.

## Files produced

- `GPT_ASTRA_REDELBE_BRIEF.md`: complete copy-ready execution brief.
- `GPT_ASTRA_KULA_RE9_BRIEF.md`: separate copy-ready execution brief.
- `inspect_redelbe.py`: reproducible read-only inspection script.
- `analysis/redelbe_static_triage.json`: detailed hashes, imports, sections, and per-pattern results.

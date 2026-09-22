# Legacy texture restoration investigation

## Subsequent Hanabi installation — 2026-09-16

Hanabi is now installed in the authorized LR backup as
`KashiraProjects/REDELBE_LR_Hanabi/project.ktproj`, with a built Kashira package.
It contains 41 runtime assets for KOK_COS_001, KOK_FACE_001 and KOK_HAIR_001.
The bridge restores four texture IDs and five face/hair support IDs, with eight exact
reference patches across MaterialEditor and CharacterEditor. Each referenced Vanilla
fallback is byte-identical to its current LR target. One unmapped SID is preserved only
as a source reference. The actual Editor build and full 33-mod installed sync passed.
In-game appearance and voice have not been verified. Tifa remains an offline proof.
The project-local REDELBE_Dependencies folder and bridge configuration are required;
copying only the ktmod to another installation does not install the restored resources.

The following result describes the earlier investigation before this installation.

## Result

The suggested old-hash restoration works structurally for the missing textures in the two requested test mods. **No isolation package has been installed and neither complete mod has been tested in-game.** This turn made no changes to either game installation.

| Mod | Slot | G1T files | Missing LR resources restored |
|---|---|---:|---:|
| Hanabi Hyuga (Adult) | KOK_COS_001 | 16 | 4 |
| Tifa Lockhart v2.0 (OG FF7R) | HTM_COS_105 | 41 | 18 |

The supplied MaterialEditor exports contain 52,629 old texture records and 63,002 LR texture records. 52,574 have matching object IDs; 30,897 of those have different texture resource references. Those differences are candidates for comparison, not authorization to replace every record blindly.

For the selected 22 missing textures, their original texture objects still exist in LR. Therefore, no new material objects are necessary: restore the original G1T resources under their original file hashes, then change only `KTGLTexContextResourceHash` (0x6C7321D2) in the matching LR records.

## Built artifacts and checks

`packages/legacy_texture_isolation/` contains:

- `restoration_plan.json`: exact old/new references and original payload hashes.
- `restored/`: 22 textures extracted directly from original DOA6 MaterialEditor archives, not from active mods (47,624,176 bytes total).
- `MaterialEditor.before.dok`: current LR database baseline.
- `0xd956e4a2.dok`: patched **LR** database; its version and all other records are retained.
- `overlay/root.rdb`, `root.rdx`, `data/*.file`: offline registration proof using LR's own resource-entry templates.
- `overlay_verification.json`: all 23 assets can be extracted through the generated index with matching hashes; 81,153 other index records remain byte-identical.

The database roundtrip preserves the full source byte-for-byte before modification. The patch changes 22 reference properties; 196,923 other records remain byte-identical. This avoids replacing LR's database version 14 with DOA6's version 10.

**Do not copy the generated root.rdb into the game manually.** The installed REDELBE bridge already generates an index overlay per launch. These additions must be merged into that preparation path, after Kashira applies its packages, with new-ID Vanilla fallbacks and Layer2 routes generated together. The offline overlay is evidence of registration, not a complete installer.

## Reproduction / update handling

From the research directory, using Python and .NET 8:

```text
python tools/inspect_isolation_inputs.py
python tools/audit_legacy_texture_refs.py
python tools/prepare_legacy_isolation.py
dotnet run --project tools/KashiraContract -- restore-textures packages/legacy_texture_isolation
python tools/build_isolation_overlay.py
```

The overlay builder requires a fresh output directory. Preserve previous output before rerunning. Paths currently target this user's explicit game copies and exports. After a game update, refresh the LR XML export and rerun the comparison. The patcher verifies each expected LR reference and the baseline SHA256, rejecting conflicts rather than applying stale edits.

## What remains for complete ports

- Integrate registration and restoration into Kashira/REDELBE preparation without overwriting authored material edits.
- Generate Layer2 routing for all requested files, including restored IDs, and test original appearance with mods off.
- Handle face/hair slot and work semantics. Hanabi replaces face and hair as well as costume. Tifa uses `HTM_FACE_001 -> HTM_FACE_032` work redirection, has two hair models, and its `mod.ini` costume line contains an unmatched quote. Its numerous exported mesh/DDS editing files must not become runtime assets.
- Test each mod against another character and test two-player use. Restoring old per-character hashes addresses LR's cross-character deduplication. It does not by itself provide separate textures for two players using different mods on the same original resource ID.
- The unrelated Tina 105 crash remains unresolved; the user confirmed the last test build still crashed. Its installed experimental ASI was not changed during this investigation.

## Audio result

`packages/SRSA_LR/` contains the new standalone sound tool and instructions. Original SRSxtool 1.0 failed on LR's unreadable track-name bytes; the new tool uses track IDs, preserves names/metadata, and supports embedded ADPCM/Ogg replacement. Eight LR banks passed offline tests. Installation and in-game playback are not claimed.

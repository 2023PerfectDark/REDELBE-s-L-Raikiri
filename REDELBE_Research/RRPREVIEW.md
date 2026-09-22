# RRPreview in REDELBE LR

Place extracted, named resource files in `REDELBE_LR/RRPreview`. Subfolders are allowed. Close the game and run `Sync REDELBE Layer2.cmd`, or use the REDELBE launcher, after adding, editing or removing files. ZIP/RAR archives are not loaded. Duplicate replacements for the same resource stop synchronization with an error.

RRPreview replacements are global: they do not require F and are not costume/hair Layer2 choices. To disable Moka, move the entire `Moka Announcer` subfolder outside RRPreview and synchronize again. Keep the SRSA and SRST together. Original game archives are not changed; generated overlay sets retain their Vanilla fallback.

## Moka Announcer

The source ZIP contains `SE1_Common_SV.srsa` and `SE1_Common_SV.srst`. The old bank has 776 streamed voices; LR has 802. Synchronization merges matching streamed Ogg audio into the current LR bank by voice ID, preserves LR cue metadata and retains the 26 LR-only voices. Moka changes 13 streams relative to the inspected LR bank. SRSA offsets, sizes and replacement sample counts are rebuilt from the actual Ogg data. A missing or mismatched pair is rejected.

The installed source files stay editable in RRPreview. The prepared LR-compatible banks live in the generated set. Do not inject the source banks into the RDB archives.

## Compatibility scope

The folder resolves known RRPreview filenames and explicit hash filenames to existing LR resource IDs. Signature checks are not a universal legacy-format converter. Streamed Ogg SRSA/SRST pairs have the explicit merge path above; other resource formats must already be LR-compatible. Stage/weather ports remain deferred. Only Moka was installed for this test; the unrelated original RRPreview overrides were not imported.

## Verification

Moka integration tests verify all 802 voice IDs remain, the 13 source replacements are retained, all 26 LR-only streams and cue metadata remain unchanged, self-merging is byte-identical, and malformed/mismatched pairs fail. Five existing Kashira bridge tests pass. Native DLL and portable Sync EXE build successfully. Generated overlay verification passes for all 65 mod assets and 66 Vanilla resources. The runtime log confirms both announcer resources opened through RRPreview. Listening confirmation is pending.

The portable Sync executable embeds the name table and preparation code. It does not require the developer workspace, original DOA6, Python, or saved logs on the player's computer.

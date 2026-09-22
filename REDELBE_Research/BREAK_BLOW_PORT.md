# LR break-blow restriction patch

## Confirmed working, 2026-09-18

User confirmed the restriction still exists in unmodified LR. Main installed DLL SHA256: 051aa0c1edc46b83d3129c7b13b6849674b26ef27b7fb560f84ce72874f6f66e.
Checkpoint: REDELBE_LR/install_backups/roster_20260918_133659. User INI additionally saved as REDELBE.ini.before_breakblow_20260918_133659 (timestamp may differ by a second).

`[Uncensorship] uncensor_loli_blow=true` enables the optional patch; false leaves original code untouched on a fresh launch. Restart required. Main startup log confirms the patch applied. User confirmed the effect works for HON/MAR/NIC/SNK and Minato (MNT).

## Evidence and semantics

Original reference: Patches/uncensorship.xml. Original runtime patch site RVA 0x19d9266 in routine 0x19d9220; the existing REDELBE was observed applying xor edi,edi / jump. The function checks an opposing character property through 0x1972960, which tests property 0x202. It then conditionally performs the camera override with words 0x101, transition argument 8 and player index. The original XML forces this character check's result false while preserving the earlier global option branch.

LR equivalent: routine 0x3aeacf0 (updated) / 0x3b09b80 (baseline), with the same script advance of 4, player index at 0x3560, opposing-player XOR, global camera option, property check, and camera override output. LR removed the old threshold branch. Its property routine at 0x3a6dee0 / 0x3a8cd70 also tests property 0x202.

LR patch changes only opcode 0x74 to 0xEB at function offset 0x46, preserving displacement 0x4B. This forces the skip-camera-override branch after the property check. It does not alter the earlier global option branch or patch the property function for unrelated callers. No on-disk game EXE is changed.

## Validation

Generated relocation-masked signatures cover the full branch routine including chained unwind segments, plus the property function. Both match uniquely in the baseline and updated saved images. Runtime also verifies the property call target and final return destination. On no match or ambiguity only this optional patch is skipped and logged.

C++ tests pass for both builds; modified instruction, duplicate function-table match, changed call target, and already-patched branch are rejected. Config parser tests pass. Startup logs captured in evidence/break_blow_startup.log. Pattern evidence: evidence/break_blow_patterns.json; original disassembly: analysis/breakblow_original.asm.txt. Original memory snapshot is local research only, not included in release files.

Original DOA6 was launched for read-only comparison and closed before launching LR. No original game files were modified. Existing public release ZIP remains unchanged; settings kit updated.

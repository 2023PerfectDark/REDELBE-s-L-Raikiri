# LR 1.10 Layer2 hook evidence

Executable SHA-256: 35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea

All offsets are RVAs in `lr_baseline.bin`; runtime code also checks full executable
and archive fingerprints and every overwritten prologue before installation.

## Cycling

- model::request_character_with_id script wrapper 0x37dc1d0 calls 0x22c8270.
- layout::play_anime wrapper 0x37d6140 jumps to 0x21beda0.
- Cache tests at 0x22c6220 and 0x22c6260 are bypassed only while explicitly
  re-requesting a model after cycling. Controls were visually user-confirmed.
- Keyboard callsite 0xe4aea3, DirectInput GetDeviceState vtable index 9, F scan 0x21.
- XInputGetState IAT cell 0x41baa80; Back rising edge goes backward, left trigger
  rising edge >128 goes forward. 350 ms debounce across sources.

## Random selection

Original REDELBE PatchSRVS and PatchSRFT instruction fragments lead to LR callers:

- 0x39a7c5c calls 0x3919430, return 0x39a7c61; object member +0xd0 (Versus).
- 0x39b0fd7 calls 0x3919430, return 0x39b0fdc; object member +0xa0 (Free Training).
- 0x39929d3, object member +0x138 (Arcade/TA); excluded.
- 0x39952b2, object member +0x140 (Survival); excluded.
- 0x39ad8d7, object member +0xd8; unidentified variant, excluded.

The shared function's first 15 bytes are whole instructions without RIP-relative
addressing. At 0x3919509 it copies the result's costume hash to output+4. Other
fields and a new tail structure follow; the hook reads only the costume hash.
It calls the real game routine first and preserves all eight arguments and its
return. It draws Default or one catalog entry only at the two allowed return RVAs.

The two active costume IDs drive resource lookup; the catalog is not scanned for
every open. Native-ID resource sharing between players is still a limitation;
same-costume players with different mods need additional engine-level identity
handling. No claim of complete two-player compatibility is made.

The user confirmed the first Random match loaded normally. Its log showed two
generated results per player in Versus, demonstrating that activation directly
in this hook would apply a future result prematurely. The corrected build queues
choices and activates only on matching character, costume, face, and hair.

Constructor candidate 0x2a3f740 preserves R9 (slot), R8B (character), RDX (context).
It stores the character at object+0x3ac and copies slot fields to object+0xb8.
Its first 16 bytes are whole instructions without relative addressing. The new
load hook reads the first 12 slot bytes and otherwise preserves the call. Live
Versus validation now confirms queue consumption and a modded result; the user
reported Random works. See evidence/layer2_random_confirmed.log.

## Full preview reload after manual cycling

The original REDELBE calls model_request_character_with_id with cache reuse
disabled; it has no three-second sleep. LR's outer checks at 0x22c6220/0x22c6260
set rebuild flags but do not by themselves prevent inner async request reuse.
The body/face loader 0x22dca70 calls 0x22c6310 and returns early on a cache hit.
The hair loader 0x22dcc60 similarly calls 0x22c63b0. Both checks now return false
only within the thread-local manual reload scope. Normal and Random loads retain
their existing behavior. Actual lifetime/visibility remains managed by the game.

New prologues are 14 and 15 bytes respectively, ending before RIP-relative LEA.
All eight hooks passed saved-image byte and complete-instruction validation.
`LAYER2 PREVIEW RELOAD ... cache_misses=a,b,c,d` reports the four bypass counts.
Compilation and installation succeeded; disappearance/reappearance needs the
user's visual test. No fixed delay or background thread calls into game objects.

Installed ASI SHA256:
723d5918d478318de4ceb575694f7132c3d26062ae06b30ef1926a4a7a4c7afc
Pre-change full backup: backups/20260915_232350_935.

### Body cache correction — confirmed

Four cache misses caused disappearance/reappearance and updated makeup, but the
body file did not reopen until the user changed costume slots. Native clear
0x22dbff0 takes the request handle in RDX. It marks the old request cancelled,
clears its shared pointer and releases ownership, and destroys its pending
callback. RCX is unused. The body handle is model+0x98+player*0x2d8, established
by 0x22c8270; face and hair handles are separate. Its first 15 bytes are checked
before enabling the feature. The higher-level model::reset was inspected and
not used: it resets both players and includes unrelated material state.

Manual cycling calls this native clear for the selected body and schedules a
300 ms non-blocking wait. Existing input hooks resume the saved request on the
same initiating thread, with four cache checks bypassed. Natural preview requests
cancel pending manual work; costume-screen exit completes it early on that thread.
No worker thread calls game objects, and no game memory is manually freed.

User: 'Outfits changed correctly; I closed the game'. Log corroborates body
file reads after all 27 cycles across AYA_COS_001/105. Other players, rapid menu
transitions, and extended stability are not covered by this visual confirmation.
Current SHA256: f466ca07f43c081a418658ddcd4e149a336ba1570cc32414ed72b80428d12211.
Confirmed checkpoint: backups/layer2_body_reload_confirmed.

## Costume/mod caption

The named script binding `layout::set_pane_text_utf8` at 0x37fd0e1 points to
wrapper 0x37d6180, which calls native setter 0x21c1e90. Its first 14 bytes are
fingerprinted before use. RCX is the same layout object used by play_anime
(both wrappers reference global 0x5e5a2a8); capture it in the existing layout hook.
RDX is unused, R8 pane hash, R9 zero, stack arg 5=4, arg 6=UTF-8 text. The setter
converts/copies text synchronously. Use pane 0xf121f112, as original REDELBE does.

Update after costume requests, immediately on manual cycling, on cos_in_p1/p2,
and caption_in. Only the active costume-screen player is displayed. Do not write
labels for random match loads. Costume names come from the local DOA6LR.csv,
hashed as game slot strings (not model file resource IDs). 623 distinct names
without collisions; unknown hashes remain visible as hexadecimal. UI visibility
and long-name fit require visual confirmation.

Evidence: random_candidates.json, random_routine.asm.txt, and
evidence/layer2_random_first_match.log. A confirmed pre-random ASI and source
checkpoint are in backups/layer2_controls_confirmed.

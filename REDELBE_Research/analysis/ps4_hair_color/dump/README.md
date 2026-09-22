# PS4 update dump results

Extracted 27 package-table entries from the full update (metadata resides in part 0) and 15 from the delta package. Continuation parts 1-7 contain the remaining payload, not separate package entry tables.

Raw entry dumps and JSON manifests are in the two package-named folders. Encrypted entries are explicitly named encrypted. Key-index-3 outer AES layers were processed separately; outer_decrypted does not mean the inner filesystem key or game payload was decrypted.

The readable changeinfo.xml confirms PS4 APP_VER 01.26 added hair-color changes using Premium Tickets.

No decrypted eboot.bin, hair textures, palettes, or implementation code were obtained. The PFS remains encrypted and the fake-package key recovery failed. A valid filesystem key/package passcode or a decrypted dump from a system able to load the game is required to continue inspecting these game resources.

Original packages and the installed game were not modified.

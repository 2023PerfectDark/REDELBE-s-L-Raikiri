# Yellow aura research — NOT an installable mod

Status: original resources extracted and verified; yellow recolor and private effect routing not implemented.

The references folder contains unchanged LR aura resources with readable names and a SHA-256 manifest. Do not inject these as a yellow mod: they are still the vanilla red/black aura.

Body KTID 69848a36 resolves texture contexts 39fc500d, 1ddfc7f4, 07072dbf, 4fba76c5 to resources 67eeced6 (albedo), 445c5b59 (reflection), ebee8364 (normal), 7589067d (occlusion). Contexts occur in CE1CommonResource.motor and Field_Common.character.level databases. Shared reflection/occlusion resources should not be globally recolored.

G1E files use XF1G5200. Their color fields are not verified. Do not blanket-replace floating-point values: these files also contain transforms, lifetimes and relative offsets.

Native inspection: effect vtable RVA 4be3530; virtual draw entry 34029a0 forwards to 3402a90. Function 3406c90 iterates runtime groups (stride f0, count at c8) and calls 114fc40; that function stores a parameter pointer at group+88+index*8. Parameter meanings and ownership have not been established; no calls or memory writes were attempted. Evidence is in analysis/aura_draw_color.txt and analysis/aura_parameter_setters.txt.

Next: verify the particle color/curve schema or a native per-instance color override, then provide unique effect resources/instance routing for the selected Layer2 mod. Test Hayabusa alongside native Raidou to check isolation.

No live game files, loader binaries, mod settings or Kashira packages were changed during this investigation.

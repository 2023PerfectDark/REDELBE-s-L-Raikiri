# Hair/head Layer2 — RC4 test

## Controls

In costume selection, F or L2/LT cycles costume mods and Select/Back goes backward.
In the hair/details menu, the same controls cycle the selected hair/head group.
The caption shows `Hair: KAS_HAIR_002 Mod: ...`. Each group starts at Vanilla.
Hair choices are independent of costume choices and keyed by player, hair, and face.
An explicitly selected hair/head package takes precedence over overlapping assets
in a costume package. Selecting Vanilla removes that explicit override; an active
costume bundle can still supply its own face/hair assets.

## Installed examples (main game)

- Eve ponytail: Kasumi `KAS_HAIR_002`, 7 assets. Project: `KashiraProjects/REDELBE_LR_Eve_Ponytail/project.ktproj`.
- Hanabi Hair 1 / Adult Byakugan: Kokoro `KOK_HAIR_001`, 17 visual assets. Project: `KashiraProjects/REDELBE_LR_Hanabi_Hair_Head/project.ktproj`.

Both packages are in `_Kashira/Mods`, disabled in-game until selected. Kashira
profiles still control whether each package is available in the catalog.
Hanabi's original audio/facial-animation extras were excluded from this visual test.
Its five absent original resource IDs are restored by the project dependency plan;
vanilla fallbacks were copied from the corresponding current LR resources.
These example assets are not included in the public loader ZIP.

## Editor/bridge

Explicit Layer2 markers accept COS, HAIR, or FACE slot names. A FACE-only package
is offered in the hair menu while its matching face is in use. The bridge also
recognizes unmarked legacy packages by native mesh-to-slot mappings; costume
bundles keep their costume as primary, and hair/head bundles use the hair slot.
Ambiguous slots and authored material manifests still require explicit preparation.
Texture-only packages need an explicit marker because their intended slot cannot
be determined reliably from a mesh that is absent.

## Validation

Selection-state regression tests and five bridge tests pass. The native pattern
set is unchanged from RC3. Five installed mods / 63 mod assets / 64 fallback
assets verified during preparation. User confirmed Eve hair caption/cycling and Hanabi hair, Byakugan face textures, and return to Vanilla. The log shows tests on both player slots.

Rollback: main game `REDELBE_LR/install_backups/hair_20260917_211114`.
The older backup installation and original source mod folders are unchanged.


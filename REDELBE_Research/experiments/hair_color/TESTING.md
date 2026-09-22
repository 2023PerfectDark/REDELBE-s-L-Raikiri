# Hair Color — DOA Central test

This is an experimental build, not the completed public hair-color system.

## Open the palette

In the main LR copy, open **DOA Central → Wardrobe → Hitomi → Custom Slot 1**.
Confirm the slot to open the Costumes / Hairstyles / Glasses / Titles panel.
Click **Hair Color** at the bottom of that panel. Select a color to apply it.
**Default** restores the original albedo; **Back** closes the palette.

The palette contains Default, Blonde, Red, Blue, Silver, Pink, and Black.
Mouse selection is visually verified. Y / H open the palette; D-pad / arrows
navigate, A / Enter apply, and B / Escape close it. These keyboard/controller
bindings still need hands-on verification with the user's primary input setup.

## Current scope

- Hitomi and Kokoro: 12 catalog entries, eight unique vanilla hair albedos.
- Immediate recoloring verified on Hitomi's Hachimaki: Blonde, Red, Blue, Default.
- Original strand transparency is retained. Hitomi's white headband, face and
  outfit retained their appearance in the visual tests.
- Choices are stored separately from the game save in
  `REDELBE_LR/HairColors.prototype.ini`, by character hash and custom-slot index.
- Verified: Blue restores after a fresh game launch. Hitomi Slot 1 keeps Blue
  while Slot 2 independently keeps Red. The native main-fighter slot getter was
  unsuitable; the editor now tracks native custom-slot cursor events.
- Verified: closing the palette and right-clicking back to slot selection works.
- The UI is a REDELBE-owned overlay positioned in the custom-slot panel. It is
  not a restored PS4 native menu tab. No premium tickets are involved.
- Colors currently apply only in the DOA Central editor. Match application,
  complete roster coverage and exclusive fullscreen behavior remain unfinished.
- Explicit Layer2 texture replacements take precedence. This build does not
  recolor arbitrary mod textures.

## Stability

Intermittent startup exits occurred during development, including before this
feature was installed. One later title-screen stall was also observed. These
issues have not been established as fixed. Do not distribute this test build.

## Installed files

The main game's `dinput8.dll` is the test loader. Its active resource set is
`REDELBE_LR/sets/hair_color_research_01`. Original game archives are unchanged.
The existing seven Layer2 mods and their assets passed package verification.

## Roll back

With the main game closed, restore `rollback/dinput8.dll` to the game root and
`rollback/active_package.txt` to `REDELBE_LR/active_package.txt`. These restore the
loader and package selection that were active before this experiment.
The original package and the research package both remain on disk.

## Development files

Source and build scripts are in `native_test`. `prepare_preview.py` creates a new
research package from an existing active package and an extracted MaterialEditor
XML. This XML-based preparation still needs integration into the portable bridge.
`check_texture.py` verifies real-texture mip and alpha preservation.

Texture decoding uses [bcdec](https://github.com/iOrange/bcdec); its source and
license are included under `native_test/third_party`.

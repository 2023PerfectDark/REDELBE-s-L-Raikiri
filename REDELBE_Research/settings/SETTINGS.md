# REDELBE LR settings

Edit `REDELBE_LR/REDELBE.ini` with a UTF-8 text editor while the game is closed. Restart the game to apply changes. Missing or invalid values use defaults; invalid values are reported in the loader log. Section/key names are case insensitive. Use true or false for switches.

## Roster

Under `[UI]`, use the **Custom roster animations** switch:

- `character_roster_transitions = true`: custom Accessories transitions, handoff fade and highlighted-portrait reveal.
- `character_roster_transitions = false`: original game roster animations and visibility. All custom roster options below are ignored.

Restart the game after changing this switch. The launcher should disable its dependent roster controls while it is Off. Your saved custom settings remain available when you turn it On again.

The custom controls are:

- `roster_accessories_exit = native` (or instant)
- `roster_accessories_return = native` (or instant)
- `roster_handoff = fade` (or instant), when Player 1 is ready
- `roster_fade_ms = 10000` (100–10000 milliseconds)

The Player 1-ready handoff now fades over 10 seconds. `roster_hover_reveal = true` makes the portrait under the P2 cursor appear immediately; moving away hides it, then it fades back over the remaining time. Selecting Player 2 ends the fade. Set this switch false for a uniform fade. Confirmed working in-game by the user.

## Break-blow close-ups

`[Uncensorship] uncensor_loli_blow = true` bypasses the character restriction on break-blow facial close-ups. Set false and restart for vanilla behavior. Unknown or changed code skips only this patch and logs the reason. Confirmed in-game for Honoka, Marie Rose, NiCO, Kula, and Minato.

## F5 battle HUD

`[UI] enable_hide_battle_hud = true` enables the F5 shortcut. Press F5 once to hide HUD groups and again to restore them. The game starts with the HUD visible. The shortcut is independent of Layer2 keyboard controls. Set false and restart to disable it; with false, F5 is passed through to the game.

The layout list follows original REDELBE and includes battle, training, tutorial, replay/photo overlays and its shared scroll/marker groups. Native hide requests are tracked so F5 does not revive groups the game deliberately hid. Holding F5 triggers only once. Confirmed working in-game by the user.

## Other working settings

`[Misc] slot_info_in_css` controls costume/hair codes and mod labels.
`[Misc] slot_info_in_sss` controls stage slot labels (for example, Sweat is `S1301GYM`). Named stages show `Mod: Vanilla`; stage Layer2 loading remains unported. Random has no fixed slot. Random and fallback stage previews show `Slot: Random Vanilla Stage/Modded Stage`. This caption does not enable stage mods. Restart after changing this option. The user confirmed stage captions work in-game.
`[Layer2]` controls costume cycling, hair/head cycling, keyboard and gamepad input independently. Mods still start on Vanilla.
`[Random] enable_random_costume_mods` controls Layer2 choices during Random character selection; false selects Vanilla.
`[Branding] enabled` controls whether the loader title label is shown. Loader name and version are not user-facing launcher settings.
`[Debug]` offers resource and UI logs. Basic startup/errors remain logged.

## Original DOA6 features

Every active option from the supplied original INI is retained. UNAVAILABLE entries have no effect in LR and must appear disabled in a launcher. This includes random music, stage mods, random hair/glasses/underwear, and other unported patches.

`fullmix.ini` and `random_tracks.txt` are preserved companion configuration files. They do not enable music randomization by themselves. The original XML patches reference DOA6 hook functions and instruction patterns; they are research inputs, not patches that this LR loader executes.

The Optional Extras contain Random Costume presets and Story mode stage Layer2 presets, including stage slots and disable_npc flags. These require LR stage support before use; copying them does not enable random stages.

## Launcher integration

Read `settings.schema.json`. It is metadata for an INI, not a JSON Schema validator. `formatVersion` versions the contract. Each setting has a stable section/key/id, type, default, label, description, availability, and restart requirement. Numeric bounds, enum choices and dependencies specify controls. maxLength counts UTF-8 bytes. Show unsupported settings disabled, with their reason. `companionFiles` identifies additional editable files and their availability.

Save only changed keys, preserve unrelated sections/keys/comments, and write atomically through a temporary file in the same directory. Use lowercase true/false and enum values. Do not overwrite the whole file with defaults on upgrade. Resolve all paths relative to the selected game directory. The game needs no Python, original DOA6 installation or developer files to read these settings.

This settings build does not change Kashira's own settings. Existing public release ZIPs are not updated by this development installation.

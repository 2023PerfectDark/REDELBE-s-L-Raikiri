# Expanded hair palette test

This build contains the requested 16-color grid and prepared assets for 92
hairstyles across 24 character codes. It is not full-roster or match support yet.
Colors currently route through the DOA Central custom-slot editor only.

All 840 generated variants passed container checks and cross-color alpha
consistency checks. Startup has been unreliable; the new grid has not yet been
visually verified. Shared-material isolation remains unverified. Do not release.

Expected menu path: DOA Central > Character > Custom Slot > slot details > Hair
Color. Click the entry or use Y/H. Navigate the 4x4 grid with D-pad/arrow keys;
A/Enter/click applies, B/Escape/right-click closes. Default uses original hair.
Old prototype saves remain in Colors; the new palette writes Colors16.

Installed target: REDELBE_LR/sets/hair_palette16_roster_01.
Backup: experiments/hair_color/rollback/palette16_before contains the previous
working dinput8.dll and active_package.txt. With the game closed, restore both
to their corresponding game paths to revert. Original archives are unchanged.

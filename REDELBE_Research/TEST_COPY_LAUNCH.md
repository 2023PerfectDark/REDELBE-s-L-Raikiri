# Launching the Last Round test copy

Steam's **Play** button is configured to run the test copy through this launcher:

`G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415\REDELBE_LR_Launcher.exe`

The launcher starts the adjacent official `DOA6LR.exe`, sets its working directory
to the same folder, inherits Steam's environment, and waits for it to exit.
It does not bypass Steam checks, convert assets, or implement Layer2.

## Why it is needed

Opening the copied game EXE directly caused Steam to relaunch the original game.
Setting Steam to run the copied EXE directly preserved the original working
directory, so resource requests missed the prototype's redirects. The launcher
fixes both path problems. Both process path and working directory were verified,
and the prototype logged shadow `root.rdb` redirection in the copied folder.

## Costume test

Select Ayane's `AYA_COS_001` or `AYA_COS_105` costume. Prototype 0.2 starts with the normal costume.
Press **F** or **L2/LT** to cycle forward; **Select/Back** cycles backward.
The installed collection has 6 mods on `AYA_COS_001` and 15 on `AYA_COS_105`,
plus Default in each list. The user confirmed all three controls with the original
test mod. Restarting the game resets all choices to Default.
See `LAYER2_0.2.md` for package format, random-selection testing, and limitations.

## Return Steam to the original installation

Open Last Round's Steam Properties, General, and clear **Launch Options**.
Its original value was empty. Leave the original game folder intact.

## Build

Run `prototype\build_launcher.cmd` using the installed Visual Studio 2022 toolchain.
Source is `prototype\test_launcher.cpp`. Configuration changes are backed up under
`backups\steam_test_launch_*`; do not restore an entire old Steam configuration
over current settings just to change this single launch option.

# Development backup — 2026-09-23

This repository backs up source and selected research notes for REDELBE LR.
The current loader is in REDELBE_Research/experiments/hair_color/native_test.
Audio editor and synchronization sources are in REDELBE_Research/tools.
Public release assembly scripts are package_alpha152.py and clean_alpha152_release.py.

## Restore
Clone this repository. Install the compiler and Python build dependencies described
in the build scripts. Supply your own game, Kashira tools and any test mods.
Some historical scripts contain machine-specific paths: review them before running.
Historical STATUS/research documents describe older experiments and are not a
statement of the latest shipped behavior. Alpha 152 source is the current checkpoint.

## Excluded from this source backup
Game executables/assets, extracted textures/audio/animations, third-party mod
packages, generated palettes, downloaded dependencies, binary releases and duplicate
builds are not stored in Git. They have NOT been deleted locally. This is not yet a
complete backup of the entire research workspace and does not authorize deleting it.
BACKUP_MANIFEST.json contains SHA-256 hashes for each copied source/research file.

Latest implementation and verification status: REDELBE_Research/CURRENT_DEVELOPMENT.md.

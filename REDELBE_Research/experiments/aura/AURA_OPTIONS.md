# Aura options (test build)

All characters can receive the added Raidou aura on either battle side. The native Raidou aura is preserved; this option does not remove his built-in effect. Other native effects are preserved.

## Main switch
In REDELBE_LR/REDELBE.ini:

```ini
[Aura]
enabled = true
```

Use false to leave added auras off by default. The current test installation uses true for both fighters.

## Per-Layer2 mod switch
Add this section to a character costume or hair/head mod.ini:

```ini
[Aura]
enabled = true
```

Use false to disable the added aura for that selected mod. Omit the section to inherit the main setting. Hair/head settings override costume settings. Vanilla inherits the main setting. Inactive mods do not affect the aura.

The loader reads mod.ini beside that selected mod's generated redirects.tsv in the active package. Kashira Sync can regenerate those files. For a persistent user override, create:

REDELBE_LR/Layer2/<exact name shown in the mod caption>/mod.ini

This sidecar may contain only the Aura section. It overrides the generated mod.ini and survives package regeneration. It is a settings file, not an instruction to port assets or install another mod. Archive-internal Kashira options are not automatically imported by this change.

Settings are evaluated when battle fighters initialize. Enter a new match after changing the setting or mod selection. This version does not toggle an existing aura live while cycling costumes in character select.

The custom audio uses one loop shared by both fighters, follows Game SE, and respects pause. AuraSound remains its separate volume/file switch. Two fighters do not double the audio volume.

Both-side visuals and per-mod activation require in-game verification. This remains an executable-version-guarded test build.

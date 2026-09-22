# Automatic character Layer2 isolation

Close the game after adding, removing or editing mods, then run **Sync REDELBE Layer2.cmd**. Supported character mods are prepared with separate model, material and texture references. They remain Vanilla until selected through Layer2.

- Kashira: use the normal supported Layer2 package/project workflow and active profile.
- Loose mods: place LR-compatible assets and mod.ini under REDELBE_LR/Layer2/Mod Name. The importer also reads REDELBE/Layer2.
- Costume and separately selected hair/head mods can be combined; the hair/head selection takes precedence for the parts it replaces.
- Each generated package contains private_models.json describing preparation success or the reason isolation was unavailable.

This is not a universal DOA6-to-LR converter. Unknown resource names, unregistered assets and unsupported package formats need a port. If a recognized character mod cannot be privately cloned, it retains classic Layer2 activation and Sync reports the reason; classic redirects may still conflict. Stage/weather isolation is outside this feature.

Hanabi's migrated legacy bindings travel in its project/package metadata; no original DOA6 installation or research scripts are needed at runtime. Do not remove redelbe_layer2.json from the prepared project.

Validation: Hanabi versus Vanilla Kokoro was visually confirmed in selection and battle with explicit fighter routing. Automatic preparation passed for seven installed character mods, with RRPreview preserved; broader in-game regression of the generated catalog remains pending.

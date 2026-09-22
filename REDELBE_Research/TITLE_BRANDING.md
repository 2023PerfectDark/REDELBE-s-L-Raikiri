# Editable title branding

RC3 title branding is user-confirmed on Ver. 1.11 (2026-09-17).

Intended configuration: `REDELBE_LR/branding.ini`, UTF-8 text:

```ini
[Branding]
Enabled=1
Name=Raikiri
Version=0.3 RC3
```

The game version is preserved. The name and displayed loader version can be changed
without rebuilding the DLL. Settings are read when the version text is set again;
return to the title screen or restart the game after saving. `Enabled=0` hides only
the loader label. Keep names short to fit the native version pane.

Configuration is generated only if missing and is not an installer-owned payload,
so loader upgrades preserve custom names.

Implementation uses the native UTF-16 pane setter, resolved by a relocation-masked
function pattern verified against the old and Ver. 1.11 runtime images. No permanent
changes to the game executable or UI resource files are required.

The observed version string is `Ver. 1.11 ` (including a trailing space).
Matching is restricted to title pane 0xb281b468 and version-only text; copyright
and other menu text are preserved. Temporary tracing has been removed.
The user confirmed that the full label is visible and correctly positioned.


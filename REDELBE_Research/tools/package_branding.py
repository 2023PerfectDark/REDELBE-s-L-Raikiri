from pathlib import Path
p=Path('tools/package_portable.py');s=p.read_text().replace('0.3_RC2','0.3_RC3').replace('0.3 RC2','0.3 RC3');s=s.replace('\nEDITOR\n','''
TITLE NAME
The title version line includes Raikiri 0.3 RC3. After the first launch, edit
REDELBE_LR/branding.ini in Notepad (save as UTF-8):
[Branding]
Enabled=1
Name=Raikiri
Version=0.3 RC3

Change Name and Version whenever desired; restart the game to apply reliably.
Enabled=0 hides the loader label. Keep names short to fit the native pane.
The game version remains intact. Your branding.ini is preserved during upgrades.

EDITOR
''');p.write_text(s)
p=Path('TITLE_BRANDING.md');s=p.read_text().replace('Current test: text tracing is enabled to locate the exact version pane. Remove the\ntrace and confirm native label placement before distributing the branding build.','The observed version string is `Ver. 1.11 ` (including a trailing space).\nMatching is restricted to title pane 0xb281b468 and version-only text; copyright\nand other menu text are preserved. Temporary tracing has been removed.\nVisual fit is awaiting user confirmation.');p.write_text(s)

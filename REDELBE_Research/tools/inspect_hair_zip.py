import zipfile
from pathlib import Path
p=Path(r"G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415\_Kashira\Mods\(Hair) ~LR~ Stellar Blade Eve's Ponytail 1 (Kasumi).zip")
with zipfile.ZipFile(p) as z:
 for i in z.infolist():print(i.filename,i.file_size)

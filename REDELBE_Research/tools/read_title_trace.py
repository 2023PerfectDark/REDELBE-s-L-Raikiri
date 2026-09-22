from pathlib import Path
p=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round\REDELBE_LR\loader.log')
for line in p.read_bytes().splitlines():
 if b'pane=b281b468' in line:print(repr(line))

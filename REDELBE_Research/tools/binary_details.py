import sys, json, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent/'python_deps'))
import pefile
b=Path(__file__).resolve().parents[1]
paths={'reference':Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6\DOA6.exe'),'target':Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round\DOA6LR.exe'),'loader':b/'original/dinput8.dll'}
report={}
for key,p in paths.items():
    data=p.read_bytes(); pe=pefile.PE(data=data)
    imports={d.dll.decode():[{'name':i.name.decode() if i.name else '#'+str(i.ordinal),'rva':hex(i.address-pe.OPTIONAL_HEADER.ImageBase)} for i in d.imports] for d in pe.DIRECTORY_ENTRY_IMPORT}
    report[key]=dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),imports=imports)
    print(key,report[key]['sha256'])
    if key=='target':
        print(json.dumps(imports,indent=2))
(b/'analysis/binary_details.json').write_text(json.dumps(report,indent=2))

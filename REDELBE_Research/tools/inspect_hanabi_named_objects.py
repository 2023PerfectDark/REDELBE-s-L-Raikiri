"""Extract readable schema clues from supplied XML; never use XML as a patch baseline."""
import json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415\6LR kidsobjdb xml.zip')
out={}
with zipfile.ZipFile(source) as z:
 for name in ('xml/CharacterEditor.kidssingletondb.kidsobjdb.xml','xml/CharacterEditor.shader.kidssingletondb.kidsobjdb.xml','xml/MaterialEditor.kidssingletondb.kidsobjdb.xml'):
  selected=[]
  with z.open(name) as f:
   for event,node in ET.iterparse(f,events=('end',)):
    if node.tag!='Obj':continue
    label=node.attrib.get('Name','').upper()
    if any(x in label for x in ('KOKCOS001','KOKFACE001','KOKHAIR001','KOK_COS_001','KOK_FACE_001','KOK_HAIR_001')):
     selected.append({'attributes':node.attrib,'properties':[p.attrib for p in node.findall('Prop')]})
    node.clear()
  out[name]=selected
(ROOT/'analysis/isolation/hanabi_named_objects.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:len(v) for k,v in out.items()}))

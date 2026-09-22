import zipfile,io
from pathlib import Path
exec(Path('tools/inspect_hair_zip.py').read_text().split('with zipfile')[0])
with zipfile.ZipFile(p) as outer:
 with zipfile.ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as z:
  for i in z.infolist():
   print(i.filename,i.file_size)
   if i.filename.endswith('.json'):print(z.read(i).decode())

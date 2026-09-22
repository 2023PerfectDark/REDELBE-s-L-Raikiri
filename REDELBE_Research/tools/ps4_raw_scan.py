from pathlib import Path
import json
root=Path(r"G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round")
stem="UP4108-CUSA12153_00-DOA6FULLGAME0000-A0126-V0100"
patterns={"elf64":b"\x7fELF\x02\x01\x01","self_header":b"\x4f\x15\x3d\x1d","hair_color":b"hair_color","eboot":b"eboot.bin","g1t":b"GT1G","g1m":b"_M1G"}
results=[]
for suffix in ["-DP"]+[f"_{i}" for i in range(8)]:
 p=root/(stem+suffix+".pkg")
 with p.open("rb") as f:
  if suffix=="-DP": start=0; data=f.read()
  else:
   start=9961472 if suffix=="_0" else 0
   f.seek(start);data=f.read(16*1024*1024)
 hits={k:[start+i for i in range(len(data)) if False] for k in []}
 hits={}
 for name,pattern in patterns.items():
  offsets=[];pos=0
  while (pos:=data.find(pattern,pos))>=0:
   offsets.append(start+pos);pos+=len(pattern)
  hits[name]=offsets[:32]
 results.append(dict(file=p.name,offset=start,bytes_scanned=len(data),hits=hits))
Path("analysis/ps4_hair_color/raw_scan.json").write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))

"""Read Kashira.Core from the user's .NET single-file manager, not our release.

Bundle layout: dotnet/runtime Microsoft.NET.HostModel/Bundle/{Manifest,FileEntry}.cs.
Only the exact named managed assembly is copied; arbitrary paths are never extracted.
"""
import struct,zlib
from pathlib import Path
SIGNATURE=bytes.fromhex('8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae')
def core_bytes(executable):
 b=Path(executable).read_bytes();signature=b.find(SIGNATURE)
 if signature<8 or b.find(SIGNATURE,signature+1)>=0:raise ValueError('Unsupported Kashira bundle signature')
 p=struct.unpack_from('<Q',b,signature-8)[0]
 if not 0<p<len(b)-12:raise ValueError('Invalid Kashira bundle header')
 major,minor,count=struct.unpack_from('<III',b,p);p+=12
 if major!=6 or minor!=0 or not 0<count<10000:raise ValueError('Unsupported Kashira bundle version')
 def string():
  nonlocal p
  size=0
  for shift in range(0,35,7):
   value=b[p];p+=1;size|=(value&127)<<shift
   if not value&128:break
  else:raise ValueError('Invalid bundle string')
  if size>4096 or p+size>len(b):raise ValueError('Invalid bundle string bounds')
  value=b[p:p+size].decode('utf8');p+=size;return value
 string();p+=40;found=[]
 for _ in range(count):
  off,size,compressed,kind=struct.unpack_from('<QQQB',b,p);p+=25;name=string()
  if name!='Kashira.Core.dll':continue
  if kind!=1 or size>32*1024*1024 or off+(compressed or size)>len(b):raise ValueError('Invalid Kashira.Core entry')
  data=b[off:off+(compressed or size)]
  if compressed:data=zlib.decompress(data,-15)
  if len(data)!=size or data[:2]!=b'MZ':raise ValueError('Invalid Kashira.Core assembly')
  found.append(data)
 if len(found)!=1:raise ValueError('Kashira manager must contain one Kashira.Core.dll')
 return found[0]
def prepare_core(game,adapter):
 data=core_bytes(Path(game)/'Kashira-win-x64.exe');target=Path(adapter).parent/'Kashira.Core.dll'
 if not target.exists() or target.read_bytes()!=data:target.write_bytes(data)

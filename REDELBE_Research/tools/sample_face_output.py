"""Read-only facial output sampling from an evaluator-observed skeleton."""
import ctypes as C, ctypes.wintypes as W, json, re, struct, sys, time
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h
def read(p,n):
 b=C.create_string_buffer(n);got=C.c_size_t()
 return b.raw[:got.value] if p and k.ReadProcessMemory(h,p,b,n,C.byref(got)) else b''
def q(p):
 b=read(p,8);return struct.unpack('<Q',b)[0] if len(b)==8 else 0
try:
 log=Path('G:/Dead or Alive Only/SteamLibrary/steamapps/common/Dead or Alive 6 Last Round/REDELBE_LR/loader.log').read_text()
 sk=int(re.findall(r'FACIAL PLAYBACK .*skeleton=([0-9A-F]+)',log)[-1],16)
 desc=q(q(sk+8));head=read(desc,12);count=struct.unpack_from('<h',head,6)[0]
 assert 0<count<4096
 mapping=struct.unpack('<'+str(count)+'h',read(desc+12,count*2))
 indices={bid:mapping[bid] for bid in (136,143,144,145,249,383) if bid<count and mapping[bid]>=0}
 samples=[]
 for _ in range(24):
  output=q(sk+32)
  samples.append({str(bid):struct.unpack('<12f',read(output+index*48,48)) for bid,index in indices.items()})
  time.sleep(.125)
 result={'skeleton':hex(sk),'indices':indices,'samples':samples}
 Path('REDELBE_Research/experiments/animation_browser/face_output_samples.json').write_text(json.dumps(result,indent=2))
 for bid in samples[0]:
  print(bid,'range',[round(max(s[bid][i] for s in samples)-min(s[bid][i] for s in samples),6) for i in range(12)])
finally:k.CloseHandle(h)

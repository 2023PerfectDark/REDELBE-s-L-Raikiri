"""Bounded read-only reverse-pointer scan in the current DOA6LR process."""
exec(open('tools/scan_aura_effect_instances.py').read().split('pattern=')[0])
target=int(sys.argv[2],16);pattern=struct.pack('<Q',target);address=0;total=0;start=time.monotonic();hits=[]
try:
 while address<0x7fffffffffff and total<8*1024**3 and time.monotonic()-start<40:
  m=MBI()
  if not k.VirtualQueryEx(h,address,c.byref(m),c.sizeof(m)):break
  address=int(m.base or 0)+m.size
  if m.state!=0x1000 or m.type!=0x20000 or m.protect&0x101 or not m.protect&0xee:continue
  for off in range(0,m.size,4*1024**2):
   data=read(int(m.base)+off,min(4*1024**2,m.size-off));total+=len(data);p=0
   while (p:=data.find(pattern,p))>=0:
    addr=int(m.base)+off+p
    if len(hits)<200:hits.append(dict(address=hex(addr),start=hex(addr-128),context=read(addr-128,384).hex()))
    p+=8
   if total>=8*1024**3 or time.monotonic()-start>=40:break
finally:k.CloseHandle(h)
Path('analysis/aura_reverse_'+hex(target)+'.json').write_text(json.dumps(dict(pid=pid,target=hex(target),hits=hits,bytes=total),indent=2));print('References',[(x['address']) for x in hits],flush=True)

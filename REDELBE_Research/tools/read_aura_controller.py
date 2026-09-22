exec(open('tools/scan_aura_effect_instances.py').read().split('pattern=')[0])
rows={}
for addr in (0x1c1bc942270,0x1c1bc942330):
 b=read(addr,256);rows[hex(addr)]=b.hex();print(hex(addr),[(hex(i),hex(struct.unpack_from('<Q',b,i)[0])) for i in range(0,min(len(b),128),8)])
 if addr==0x1c1bc942330:
  v=struct.unpack_from('<Q',b)[0];table=read(v,32);print('callback vtable',hex(v-base),'methods',[hex(x-base) for x in struct.unpack('<4Q',table)])
Path('analysis/aura_controller_live.json').write_text(json.dumps(dict(pid=pid,base=hex(base),objects=rows),indent=2));k.CloseHandle(h)

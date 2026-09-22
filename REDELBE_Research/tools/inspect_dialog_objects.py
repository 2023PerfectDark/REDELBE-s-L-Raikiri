"""Read-only roster layout/pane inspection using the main-game process."""
exec(open('tools/inspect_preview_objects.py').read().split('try:')[0])
try:
 mods=(W.HMODULE*1024)();needed=W.DWORD();ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3)
 base=mods[0];name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name))
 assert name.value.lower().endswith('\\dead or alive 6 last round\\doa6lr.exe'),name.value
 b=Path('analysis/lr_updated.bin').read_bytes();p=0x1f7b7ec
 assert b[p:p+3]==bytes.fromhex('488b0d')
 manager=u64(base+p+7+struct.unpack_from('<i',b,p+3)[0])
 head=u64(manager+0x38);node=u64(head);seen=set();entries=[]
 def successor(n):return u64(n)
 while node!=head and node not in seen and len(seen)<4096:
  seen.add(node)
  if True:
   resource=u64(node+0x18);obj=u64(resource+0x20);layout=u64(obj+0x10)
   panes=[];pn=u64(layout+0x28);pseen=set()
   while pn!=layout+0x48 and pn not in pseen and len(pseen)<512:
    pseen.add(pn);pane=u64(pn+0x10)
    panes.append(dict(world=read(u64(pane+0xe0),64).hex(),name=read(u64(pane+0xb0),min(u32(pane+0x110)&0xffff,256)).decode('utf-8','replace'),address=hex(pane),vtable=hex(u64(pane)-base),data=read(pane,0x180).hex()))
    pn=u64(pn+8)
   entries.append(dict(hash=hex(u32(node+0x10)),node=hex(node),id=u32(node+0x24),layout=hex(layout),vtable=hex(u64(layout)-base),data=read(layout,0x380).hex(),panes=panes))
  node=successor(node)
 out=dict(base=hex(base),manager=hex(manager),entries=entries)
 Path('analysis/dialog_objects.json').write_text(json.dumps(out,indent=2))
 print('menu instances',len(entries),'manager',hex(manager));print([{k:v for k,v in e.items() if k not in ('data','panes')} for e in entries[:2]])
finally:k.CloseHandle(h)



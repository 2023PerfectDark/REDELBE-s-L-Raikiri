exec(open('tools/scan_aura_effect_instances.py').read().split('pattern=')[0])
def q(p):
 b=read(p,8);assert len(b)==8;return struct.unpack('<Q',b)[0]
root=q(base+0x5ea7be8);head=q(root);node=q(head+8);seen=set();rows=[]
def visit(p):
 if p in seen or p==head or len(seen)>32:return
 seen.add(p);b=read(p,56)
 if len(b)!=56 or b[25]:return
 visit(struct.unpack_from('<Q',b,0)[0]);fighter=struct.unpack_from('<Q',b,40)[0];side=b[32]
 params=q(fighter+0x78);begin=q(params+0x188);end=q(params+0x190)
 assert 0<=end-begin<65536
 rows.append(dict(side=side,fighter=hex(fighter),params=hex(params),begin=hex(begin),end=hex(end),effects=read(begin,end-begin).hex()));print(side,hex(fighter),'effect bytes',end-begin)
 visit(struct.unpack_from('<Q',b,16)[0])
visit(node);Path('analysis/aura_fighter_effect_lists.json').write_text(json.dumps(dict(pid=pid,base=hex(base),fighters=rows),indent=2));k.CloseHandle(h)

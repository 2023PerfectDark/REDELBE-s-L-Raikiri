"""Compare texture resource references; read-only inputs, reproducible JSON plan."""
import xml.etree.ElementTree as ET,zipfile,json,hashlib
from pathlib import Path
from audit_ayane_import import names,resources,GAME
def ident(s):return int(s.split('|')[0],0)
def textures(path):
 out={}
 with zipfile.ZipFile(path) as z:
  selected=[n for n in z.namelist() if 'materialeditor' in n.lower() and n.endswith('.xml')]
  if len(selected)!=1:raise ValueError('Expected one MaterialEditor XML')
  with z.open(selected[0]) as f:
   for event,node in ET.iterparse(f,events=('end',)):
    if node.tag!='Obj':continue
    props={ident(p.attrib['Name']):p.attrib for p in node.findall('Prop')}
    p=props.get(0x6c7321d2)
    if p:
     oid=ident(node.attrib['Name'])
     if oid in out:raise ValueError('Duplicate texture object')
     out[oid]={'oid':oid,'resource':ident(p['Value']),'name':node.attrib['Name'],'type':ident(node.attrib['TypeName'])}
    node.clear()
 return out
def main():
 old=textures(GAME/'vanilla MaterialEditor.kidssingletondb.kidsobjdb.xml.zip')
 new=textures(GAME/'6LR kidsobjdb xml.zip')
 changes=[dict(oid=k,old_resource=v['resource'],lr_resource=new[k]['resource'],name=v['name']) for k,v in old.items() if k in new and v['resource']!=new[k]['resource'] and v['type']==new[k]['type']]
 mods=json.loads(Path('analysis/isolation/inputs.json').read_text());reports=[]
 for mod in mods:
  rows=[]
  for f in mod['files']:
   if not f['path'].endswith('.g1t'):continue
   ids=names.get(Path(f['path']).name.lower(),set())
   rows.append({'file':f['path'],'ids':list(ids),'present_in_lr':[i for i in ids if i in resources],
                'restorable_records':[r for r in changes if r['old_resource'] in ids],
                'old_records':[v for v in old.values() if v['resource'] in ids]})
  reports.append({'name':mod['name'],'textures':rows})
 result={'old_texture_records':len(old),'lr_texture_records':len(new),'same_oid':len(old.keys()&new.keys()),
         'changed_references':changes,'missing_texture_objects':[v for k,v in old.items() if k not in new], 'mods':reports}
 Path('analysis/isolation/reference_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print('old/lr/common/changed',len(old),len(new),result['same_oid'],len(changes))
 for r in reports:print(r['name'],'textures',len(r['textures']),'absent LR',sum(not t['present_in_lr'] for t in r['textures']), 'restorable',sum(bool(t['restorable_records']) for t in r['textures']), 'unmapped',sum(not t['ids'] for t in r['textures']))
if __name__=='__main__':main()

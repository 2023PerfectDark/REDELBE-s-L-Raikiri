"""Read-only hair-albedo ownership audit against the actual LR material database.

The XML supplies readable names only; current resource references come from the
binary DB. A matching name is not sufficient to enable a resource globally.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from dok_patch import records,props,u
from catalog_hair import catalog

def audit(xml,binary):
    candidates=[r for r in catalog(xml) if r['candidate']]
    by_object={int(r['object'],0):r for r in candidates}
    references={};verified=[]
    for rec in records(binary):
        values={key:(kind,n,pos,size) for key,kind,n,pos,size in props(binary,rec)}
        item=values.get(0x6c7321d2)
        if not item:continue
        kind,n,pos,size=item
        if kind!=5 or n!=1 or size!=4:continue
        resource=u(binary,pos)
        references.setdefault(resource,[]).append(rec[2])
        row=by_object.get(rec[2])
        if row:
            row['xml_resource']=row['resource']
            row['resource']=f'{resource:08x}'
            row['reference_changed']=row['xml_resource']!=row['resource']
            verified.append(row)
    if len(verified)!=len(by_object):raise ValueError('Some named material objects were not verified')
    for row in verified:
        other=[x for x in references[int(row['resource'],16)] if x not in by_object]
        row['other_material_objects']=[f'{x:08x}' for x in other]
        row['shared_hair_slots']=sorted({by_object[x]['hair_slot'] for x in references[int(row['resource'],16)] if x in by_object})
    return verified

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('xml',type=Path);ap.add_argument('binary',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    result=audit(a.xml,a.binary.read_bytes())
    a.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(verified_objects=len(result),unique_resources=len({r['resource'] for r in result}),with_other_material_references=sum(bool(r['other_material_objects']) for r in result))))

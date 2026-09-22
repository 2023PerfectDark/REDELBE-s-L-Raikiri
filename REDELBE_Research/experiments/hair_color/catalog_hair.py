"""Research catalog. Name-based candidates require material-reference verification."""
import argparse,json,re,xml.etree.ElementTree as ET
from pathlib import Path
def catalog(xml):
    rows=[]
    for _,obj in ET.iterparse(xml,events=('end',)):
        if obj.tag!='Obj':continue
        name=obj.get('Name','')
        match=re.search(r'MPR_Muscle_Character_([A-Z]{3})HAIR(\d{3})_([^］]+)_kidsalb',name)
        if match:
            char,slot,part=match.groups()
            values={p.get('Name','').split('|')[0]:p.get('Value') for p in obj.findall('Prop')}
            fid=values.get('0x6C7321D2')
            if fid:rows.append(dict(character=char,hair_slot=f'{char}_HAIR_{slot}',part=part,resource=f'{int(fid,0):08x}',object=name.split('|')[0],candidate=part.lower() in ('hair','hair_blend'),name=name))
        obj.clear()
    return rows
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('xml',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    rows=catalog(a.xml);a.output.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=len(rows),hair_candidates=sum(r['candidate'] for r in rows),characters=sorted(set(r['character'] for r in rows)))))

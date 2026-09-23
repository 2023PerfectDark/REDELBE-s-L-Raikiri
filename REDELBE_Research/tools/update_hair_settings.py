"""Merge the hair storage/CPU options without resetting unrelated options."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OPTIONS=[
 dict(section='HairColors',key='storage_mode',type='enum',default='full',choices=['full','cache'],label='Hair color storage',description='Full palette: approximately 27 GB. Cache: generate selected colors on demand with a 1 GB limit. Run Prepare Hair Colors after switching modes.'),
 dict(section='Random',key='enable_random_hair_colors',type='boolean',default=False,label='Random CPU hair colors',description='Offline Versus CPUs only. Requires the full palette. Does not change hairstyles or saved wardrobe choices.'),
 dict(section='RandomHairColor',key='probability',type='integer',default=35,minimum=1,maximum=100,label='CPU color probability',description='1 is a 1% chance; 100 always chooses a different custom color. Requires Random.enable_random_hair_colors=true and full storage mode.')]

def schema(path):
 data=json.loads(path.read_text(encoding='utf-8-sig'))
 for option in OPTIONS:
  row=dict(option,id=option['section']+'.'+option['key'],status='supported',apply='restart',group=option['section'],legacy=False)
  data['settings']=[e for e in data['settings'] if e['id']!=row['id']]+[row]
 path.write_text(json.dumps(data,indent=2),encoding='utf-8')

def ini(path):
 s=path.read_text(encoding='utf-8-sig')
 import re
 for option in OPTIONS:
  section,key=option['section'],option['key']
  block=re.search(r'(?ms)^\['+re.escape(section)+r'\]\s*\n(.*?)(?=^\[|\Z)',s)
  if block and re.search(r'(?m)^\s*'+re.escape(key)+r'\s*=',block.group(1)):continue
  value=option['default'];value=str(value).lower() if isinstance(value,bool) else str(value)
  text='; '+option['label']+' — LR SUPPORTED\n; '+option['description']+'\n'+key+' = '+value+'\n\n'
  if block:s=s[:block.end()]+text+s[block.end():]
  else:s+='\n['+section+']\n'+text
 path.write_text(s,encoding='utf-8')

if __name__=='__main__':
 for p in [ROOT/'settings/settings.schema.json',ROOT/'releases/REDELBE_LR_Alpha_152/_REDELBE_Runtime (Not important to you)/Data/settings.schema.json']:
  if p.exists():schema(p)
 ini(ROOT/'releases/REDELBE_LR_Alpha_152/REDELBE LR/REDELBE.ini')

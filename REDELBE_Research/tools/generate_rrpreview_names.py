"""Build-only: map original RRPreview IDs to names present in the LR name catalog."""
import argparse,json
from pathlib import Path
from legacy_resources import index
ap=argparse.ArgumentParser();ap.add_argument('original_rdb',type=Path);ap.add_argument('lr_csv',type=Path);args=ap.parse_args()
ids=set(index(args.original_rdb));names={}
for line in args.lr_csv.read_text(encoding='utf-8-sig').splitlines():
    if ',' not in line:continue
    raw,name=line.split(',',1);fid=int(raw,16)
    if fid in ids:
        key=name.lower()
        if key in names and names[key]!=fid:raise ValueError('Ambiguous resource name')
        names[key]=fid
(Path(__file__).parent/'rrpreview_names.py').write_text('# Generated RRPreview names present in both games; no user paths.\nNAMES='+json.dumps(names,ensure_ascii=True)+'\n',encoding='utf-8')
print(len(names),'RRPreview resource names')

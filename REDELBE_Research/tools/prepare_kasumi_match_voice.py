"""Prepare native LR voice-bank replacements for the active ENTRY102 test."""
from pathlib import Path
import argparse,json,struct
from srs_audio_core import Document
from srsa_lr import Bank,u
from srs_names import bank_names

root=Path(__file__).resolve().parents[1]/'experiments/doa5_victory_port'
ap=argparse.ArgumentParser()
ap.add_argument('--victory',choices=['resolve','sorry','mugen','defeat'])
args=ap.parse_args()
out=root/'match_test/Voices_102_120';out.mkdir(exist_ok=True)
lines={'resolve':{'EN':0,'JP':0},'sorry':{'EN':2,'JP':2},'mugen':{'EN':5,'JP':4},'defeat':{'EN':9,'JP':9}}
report=[]
for lang,name in [('EN','se1_common_ev_kas_us.srsa'),('JP','ev_kas.srsa')]:
    doc=Document(root/'lr_voice_banks'/name)
    for fid,row in list(doc.rows.items()):
        label=row['name'];line=None
        if '_entry_' in label:line=3
        elif '_win_' in label and args.victory:line=lines[args.victory][lang]
        if line is None:continue
        source=root/'audio_kasumi_004'/f'voice_004_{lang}_{line:02d}.wav'
        doc.replace(fid,source,match_volume=True)
        report.append({'bank':name,'cue':label,'source':source.name})
    # Native intro request cues point at the silent dummy resource. Route only
    # those two requests to an existing, replaced intro clip for this test.
    names=bank_names(doc.bank)
    dummy=next(fid for fid,n in names.items() if n=='dummy')
    spoken=next(fid for fid,r in doc.rows.items() if '_entry_' in r['name'])
    patched=bytearray(doc.a)
    for pos,e in doc.bank.entries:
        cue=names.get(u(e,8),'')
        if cue not in ('ev_kas_entry_request','ev_kas_entry2_request'):continue
        needle=struct.pack('<I',dummy); hits=[i for i in range(64,len(e)-3,4) if e[i:i+4]==needle]
        if len(hits)!=1:raise ValueError('Ambiguous intro request sound reference')
        struct.pack_into('<I',patched,pos+hits[0],spoken)
        report.append({'bank':name,'request':cue,'sound':names[spoken]})
    Bank(bytes(patched))
    (out/name).write_bytes(patched)
(out/'voice_mapping.json').write_text(json.dumps(report,indent=2))
print(f'Prepared {len(report)} voice replacements; victory={args.victory or "unchanged"}')

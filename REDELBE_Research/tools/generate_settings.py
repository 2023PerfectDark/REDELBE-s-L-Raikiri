"""Build-time catalog generation; the game needs only the DLL and UTF-8 INI."""
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6\REDELBE\REDELBE.ini')
OUT=ROOT/'settings';OUT.mkdir(exist_ok=True)
entries=[];section='';comments=[]
for raw in SOURCE.read_text(encoding='utf-8-sig').splitlines():
 line=raw.strip()
 if line.startswith('['):section=line[1:-1];comments=[]
 elif line.startswith(';'):
  if line[1:].strip():comments.append(line[1:].strip())
 elif '=' in line:
  key,value=map(str.strip,line.split('=',1));kind='string'
  if value.lower() in ('true','false'):kind='boolean';value=value.lower()=='true'
  elif re.fullmatch(r'\d+',value):kind='integer';value=int(value)
  if section=='RandomGlasses' and key!='probability':kind='list';value=[v.strip() for v in value.split(',')]
  entries.append(dict(id=section+'.'+key,section=section,key=key,type=kind,default=value,
   label=key.replace('_',' ').capitalize(),description=' '.join(comments[-8:]),
   status='unavailable',reason='Original DOA6 option; not implemented by the LR loader.',
   apply='restart',group=section,legacy=True))
  comments=[]
def supported(section,key,kind,value,label,description,**extra):
 existing=next((e for e in entries if e['id']==section+'.'+key),None)
 e=dict(id=section+'.'+key,section=section,key=key,type=kind,default=value,label=label,
        description=description,status='supported',apply='restart',group=section,legacy=existing is not None,**extra)
 if existing:entries[entries.index(existing)]=e
 else:entries.append(e)
supported('Uncensorship','uncensor_loli_blow','boolean',True,'Unrestricted break-blow close-ups','Bypass the character-property restriction on break-blow facial close-ups for HON/MAR/NIC/SNK and Minato (MNT), confirmed in-game. Uses validated LR code patterns; an unknown build skips this patch. Restart required.')
supported('Misc','slot_info_in_css','boolean',True,'Character slot and mod labels','Show costume/hair slot codes and the selected Layer2 mod in character select.')
supported('Misc','slot_info_in_sss','boolean',True,'Stage slot labels','Show the highlighted stage code in stage select. Stage Layer2 loading is not yet ported, so named stages show Mod: Vanilla. Restart required.')
supported('Random','enable_random_costume_mods','boolean',True,'Random Layer2 costumes','Include Layer2 costumes plus Vanilla in the game Random character selection, in offline Versus and Free Training.')
supported('UI','enable_hide_battle_hud','boolean',True,'F5 battle HUD toggle','Press F5 to hide or restore battle HUD and training/replay overlays. The HUD starts visible. Independent of Layer2 keyboard controls. Restart after enabling/disabling this shortcut.')
supported('UI','character_roster_transitions','boolean',True,'Custom roster animations','On: use custom Accessories transitions, handoff fade and highlighted-portrait reveal. Off: use the original game roster animations and visibility; all custom roster controls are ignored. Restart after changing.',trueLabel='On - Custom animations',falseLabel='Off - Original game animations')
for key,label in [('roster_accessories_exit','Accessories opens'),('roster_accessories_return','Back from Accessories')]:
 supported('UI',key,'enum','native',label,'Choose the normal game transition or an instant roster change.',choices=['native','instant'],dependsOn={'UI.character_roster_transitions':True})
supported('UI','roster_handoff','enum','fade','Player 1 ready → Player 2 selection','Fade or instantly show the roster when Player 1 confirms.',choices=['fade','instant'],dependsOn={'UI.character_roster_transitions':True})
supported('UI','roster_hover_reveal','boolean',True,'Reveal highlighted portrait during fade','During the handoff fade, reveal the P2 highlighted portrait immediately. Moving away hides it, then it fades back over the remaining transition. Selecting a character ends the fade.',dependsOn={'UI.character_roster_transitions':True,'UI.roster_handoff':'fade'})
supported('UI','roster_fade_ms','integer',10000,'Handoff fade duration (ms)','Length of the Player 1 to Player 2 fade.',minimum=100,maximum=10000,dependsOn={'UI.character_roster_transitions':True,'UI.roster_handoff':'fade'})
for key,label,desc in [('enable_costume_cycling','Costume Layer2 cycling','Allow manual Layer2 costume selection.'),('enable_hair_cycling','Hair/head Layer2 cycling','Allow manual Layer2 hair/head selection in Accessories.'),('keyboard_controls','Keyboard mod controls','F cycles Layer2 mods.'),('gamepad_controls','Gamepad mod controls','LT/L2 cycles forward and Select/Back cycles backward.')]:
 supported('Layer2',key,'boolean',True,label,desc)
supported('Branding','enabled','boolean',True,'Show loader title label','Display the loader name/version beside the game version.')
supported('Debug','log_virtual','boolean',False,'Log mod resource access','Log LR Layer2 overrides, Vanilla fallbacks, and resource redirects.')
supported('Debug','log_external','boolean',False,'Log loose resource opens','Log opens of LR fdata_package/data resource files; not original DOA6 RDB semantics.')
supported('Debug','log_internal','boolean',False,'Log archive container opens','Log opens of LR packed archive containers (first 4,000 opens per run). Does not trace individual packed resource reads.')
supported('Debug','log_ui_events','boolean',False,'Log UI animation events','Verbose UI tracing. Normal startup, error, selection and roster-transition logs remain enabled.')
for e in entries:
 if e['status']=='unavailable':e['readOnly']=True
 if e['type']=='integer' and 'minimum' not in e:e.update(minimum=0,maximum=100 if e['key']=='probability' or e['key']=='stage_probability' else 1000)
 if e['section']=='RandomMusic' and e['key']=='mode':e.update(type='enum',choices=['mix','full','fullmix'])
def ini_value(e):
 v=e['default']
 return ('true' if v else 'false') if isinstance(v,bool) else ', '.join(v) if isinstance(v,list) else str(v)
schema=dict(formatVersion=1,iniPath='REDELBE_LR/REDELBE.ini',encoding='utf-8',caseSensitive=False,
 apply='restart',unknownKeys='preserve',unavailablePolicy='display disabled; do not promise an effect',
 settings=entries, companionFiles=[dict(path='REDELBE_LR/'+name, status='unavailable', editable=True, description='Original DOA6 music configuration; LR music randomization is not implemented.') for name in ('fullmix.ini','random_tracks.txt')])
for name in ('fullmix.ini','random_tracks.txt'):
 (OUT/name).write_bytes((SOURCE.parent/name).read_bytes())
(OUT/'settings.schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['; REDELBE LR user settings. UTF-8. Restart the game after changes.',
 '; true/false booleans; stable section/key names for launcher integrations.',
 '; UNAVAILABLE legacy entries are retained for reference and have NO effect in LR.',
 '; See settings.schema.json for labels, types, choices, bounds and availability.','']
for sec in dict.fromkeys(e['section'] for e in entries):
 lines+=['['+sec+']']
 for e in entries:
  if e['section']!=sec:continue
  lines+=['; '+e['label']+' — '+('LR SUPPORTED' if e['status']=='supported' else 'UNAVAILABLE in LR'),'; '+e['description']]
  if e.get('choices'):lines+=['; Choices: '+', '.join(e['choices'])]
  if 'minimum' in e:lines+=['; Range: '+str(e['minimum'])+'..'+str(e['maximum'])]
  lines+=[e['key']+' = '+ini_value(e),'']
(OUT/'REDELBE.ini').write_text('\n'.join(lines)+'\n',encoding='utf-8')
def cpp(s):return json.dumps(str(s),ensure_ascii=True)
header=['#pragma once','// Generated by tools/generate_settings.py from the settings catalog.',
 'struct ConfigEntry { const char* section; const char* key; const char* type; const char* value; bool supported; int minimum; int maximum; const char* choices; unsigned maxLength; };',
 'static const ConfigEntry configEntries[]={']
for e in entries:
 header.append('{'+','.join([cpp(e['section'].lower()),cpp(e['key'].lower()),cpp(e['type']),cpp(ini_value(e)),str(e['status']=='supported').lower(),str(e.get('minimum',0)),str(e.get('maximum',0)),cpp('|'.join(e.get('choices',[]))),str(e.get('maxLength',4096))])+'},')
header+=['};']
(ROOT/'prototype/config_entries.h').write_text('\n'.join(header)+'\n',encoding='utf-8')
print(len(entries),'settings;',sum(e['status']=='supported' for e in entries),'supported')

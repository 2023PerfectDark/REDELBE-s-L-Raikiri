import json
from pathlib import Path
out=Path('experiments/mouse_menu/settings');out.mkdir(exist_ok=True)
src=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round\REDELBE_LR\settings.schema.json')
schema=json.loads(src.read_text(encoding='utf-8-sig'))
entries=[dict(id='VersusPatternParts.enabled',section='VersusPatternParts',key='enabled',type='boolean',default=True,label='Versus Pattern Parts',description='Enable the native offline Versus reward integration. Experimental until the reward popup and saved progression are verified.',status='experimental',apply='restart',group='VersusPatternParts',legacy=False),dict(id='VersusPatternParts.win_reward_mode',section='VersusPatternParts',key='win_reward_mode',type='enum',default='random',choices=['random','custom'],label='Win reward mode',description='P1 win: random 1–100 parts or the custom amount. P1 loss: always random 1–10. Parts are requested for P1’s selected character; native allocation may spill into other eligible costumes.',status='experimental',apply='restart',group='VersusPatternParts',legacy=False),dict(id='VersusPatternParts.custom_win_amount',section='VersusPatternParts',key='custom_win_amount',type='integer',default=100,minimum=1,maximum=100,label='Custom win amount',description='Pattern Parts requested for a P1 win when custom mode is selected.',dependsOn={'VersusPatternParts.win_reward_mode':'custom'},status='experimental',apply='restart',group='VersusPatternParts',legacy=False)]
schema['settings']=[e for e in schema['settings'] if e['section']!='VersusPatternParts']+entries
(out/'settings.schema.json').write_text(json.dumps(schema,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(out/'pattern_parts.ini').write_text('''
[VersusPatternParts]
; Versus Pattern Parts — EXPERIMENTAL integration; awaiting in-game validation.
; Restart the game after changes. Disable the Cheat Engine reward table.
enabled = true

; P1 wins: random 1–100, or custom_win_amount below.
; P1 loses: always random 1–10. Parts are requested for P1's character.
win_reward_mode = random

; Used only in custom mode. Valid range: 1–100.
custom_win_amount = 100
''',encoding='utf-8')

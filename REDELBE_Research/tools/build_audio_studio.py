"""Build the standalone editor. FFmpeg remains a separate executable."""
from pathlib import Path
import os,sys,shutil
root=Path(__file__).resolve().parents[1];deps=Path(os.environ.get('SRS_BUILD_DEPS',str(root/'tools/build_deps')))
output=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'packages/SRS_Audio_Studio_LR'
sys.path.insert(0,str(deps));os.environ['PYTHONPATH']=str(deps)
import PyInstaller.__main__
PyInstaller.__main__.run([str(root/'tools/srs_audio_studio.py'),'--onefile','--windowed','--collect-all','tkinterdnd2','--runtime-hook',str(root/'tools/srs_bootstrap.py'),'--name','SRS Audio Studio LR','--paths',str(root/'tools'),
 '--icon',str(root/'assets/srs.ico'),'--add-data',str(root/'assets/srs.ico')+';assets',
 '--distpath',str(output),'--workpath',str(root/'analysis/audio_studio_build'),'--specpath',str(root/'analysis'),'--noconfirm'])
dest=output/'Source';dest.mkdir(exist_ok=True)
for name in ['srs_pairs.py','srs_dnd.py','srs_bootstrap.py','srs_lr_names.py','srs_table.py','srs_library.py','srs_library_ui.py','legacy_resources.py','lr_resources.py','srs_audio_studio.py','srs_audio_core.py','srs_names.py','audio_adpcm.py','srsa_lr.py','rrpreview_audio.py','rrpreview_names.py','build_audio_studio.py']:
 shutil.copy2(root/'tools'/name,dest/name)
shutil.copy2(root/'analysis/audio/studio_verification.json',output/'verification.json')
shutil.copy2(root/'assets/srs.ico',output/'srs.ico')




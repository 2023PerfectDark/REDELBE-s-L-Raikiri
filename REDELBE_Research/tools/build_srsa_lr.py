from pathlib import Path
import os,sys
root=Path(__file__).resolve().parents[1];deps=root/'tools/build_deps'
sys.path.insert(0,str(deps));os.environ['PYTHONPATH']=str(deps)
import PyInstaller.__main__
PyInstaller.__main__.run([str(root/'tools/srsa_lr.py'),'--onefile','--console','--name','SRSA_LR',
 '--distpath',str(root/'packages/SRSA_LR'),'--workpath',str(root/'analysis/srsa_pyinstaller'),'--specpath',str(root/'analysis'),'--noconfirm'])

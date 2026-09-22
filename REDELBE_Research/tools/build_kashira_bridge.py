"""Build the standalone bridge using the local build-only dependencies."""
from pathlib import Path
import os,sys
root=Path(__file__).resolve().parents[1]
deps=root/'tools/build_deps'
sys.path.insert(0,str(deps))
os.environ['PYTHONPATH']=str(deps)
import PyInstaller.__main__
PyInstaller.__main__.run([str(root/'tools/kashira_bridge.py'),'--onefile','--console',
    '--name','REDELBE_LR_Sync','--paths',str(root/'tools'),
    '--distpath',str(root/'prototype/build'),'--workpath',str(root/'analysis/bridge_pyinstaller'),
    '--specpath',str(root/'analysis'),'--noconfirm'])

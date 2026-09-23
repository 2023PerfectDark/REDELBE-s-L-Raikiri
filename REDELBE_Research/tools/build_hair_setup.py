from pathlib import Path
import os,sys
root=Path(__file__).resolve().parents[1]
deps=Path(os.environ.get('SRS_BUILD_DEPS',root/'analysis/alpha152_build_deps'))
sys.path.insert(0,str(deps));os.environ['PYTHONPATH']=str(deps)
import PyInstaller.__main__
PyInstaller.__main__.run([str(root/'tools/prepare_release_hair.py'),'--onefile','--console','--name','Prepare Hair Colors','--paths',str(root/'tools'),'--add-data',str(root/'analysis/alpha152_hair_bundle/hair_support')+';hair_support','--distpath',str(root/'packages/Alpha152Tools'),'--workpath',str(root/'analysis/hair_setup_build'),'--specpath',str(root/'analysis'),'--noconfirm'])

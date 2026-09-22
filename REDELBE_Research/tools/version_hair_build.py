from pathlib import Path
p=Path('prototype/loader.cpp');p.write_text(p.read_text().replace('0.3 RC3','0.3 RC4'))
p=Path('prototype/layer2_runtime.h');p.write_text(p.read_text().replace('0.3 RC3','0.3 RC4'))

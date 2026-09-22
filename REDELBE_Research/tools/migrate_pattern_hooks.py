from pathlib import Path
p=Path('prototype/layer2_runtime.h');s=p.read_text()
s=s.replace('#include "layer2_model_source.h"','#include "layer2_model_source.h"\n#include "game_patterns.h"')
s=s.replace('if(caller!=0x39a7c61&&caller!=0x39b0fdc)return result;','if(reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr))+caller!=gamecode::get("randomCaller1") && reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr))+caller!=gamecode::get("randomCaller2"))return result;')
mapping={'21c1e90':'caption','22dbff0':'release','22ca6e0':'defaults','22c8270':'request','21beda0':'layout','3919430':'random','2a3f740':'load','22c6220':'cache0','22c6260':'cache1','22c6310':'cache2','22c63b0':'cache3','e4aea3':'keyboard'}
for a,n in mapping.items():s=s.replace('base+0x'+a,'gamecode::get("'+n+'")')
for a,v in {'22ca7cc':'gamecode::get("defaults")+0xec','22ca7d1':'gamecode::get("defaults")+0xf1','22cc812':'gamecode::get("scale")+0x132','22cc817':'gamecode::get("scale")+0x137'}.items():s=s.replace('base+0x'+a,v)
s=s.replace('auto cell=reinterpret_cast<void**>(base+0x41baa80);','auto cell=gamecode::xinputCell(base);')
s=s.replace('BYTE* base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));','BYTE* base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));\n    gamecode::resolve(base);\n    gamecode::xinputCell(base);')
s=s.replace('auto defaultsCall=bytes("e8 4f ba ff ff 84 c0");','auto defaultsCall=bytes("84 c0");').replace('memcmp(gamecode::get("defaults")+0xec','memcmp(gamecode::get("defaults")+0xf1')
s=s.replace('auto scaleCall=bytes("e8 09 9a ff ff 84 c0");','auto scaleCall=bytes("84 c0");').replace('memcmp(gamecode::get("scale")+0x132','memcmp(gamecode::get("scale")+0x137')
p.write_text(s)
p=Path('prototype/loader.cpp');s=p.read_text().replace('    if (hash!="35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea") { log("DISABLED: unsupported executable"); return; }','    // Validate runtime function patterns before installing any game hooks.')
p.write_text(s)

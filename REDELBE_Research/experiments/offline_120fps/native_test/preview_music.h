#pragma once
#include "preview_music_patterns.h"
static void previewMusic(bool playing) {
 if(!stageVideoUiThread||GetCurrentThreadId()!=stageVideoUiThread)return;
 using SetVolume=void(*)(void*,unsigned,float);
 static SetVolume setter=nullptr;static uintptr_t cell=0;static bool checked=false;
 static bool ducked=false;static uintptr_t duckObject=0;static float original=1,applied=1,factor=1;
 if(!checked) {
  checked=true;
  auto ini=gameRoot+L"REDELBE_LR\\REDELBE.ini";wchar_t mode[32]{};
  GetPrivateProfileStringW(L"StageVideoPreviews",L"game_music_mode",L"lower",mode,32,ini.c_str());
  if(!_wcsicmp(mode,L"mute"))factor=0;
  else if(!_wcsicmp(mode,L"lower"))factor=std::min(100u,GetPrivateProfileIntW(L"StageVideoPreviews",L"game_music_percent",20,ini.c_str()))/100.f;
  if(factor>=1)return;
  auto base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
  auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
  auto directory=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
  auto functions=reinterpret_cast<RUNTIME_FUNCTION*>(base+directory.VirtualAddress);
  BYTE* wrapper=nullptr;
  for(unsigned i=0;i<directory.Size/sizeof(RUNTIME_FUNCTION);++i) {
   auto f=functions[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress-f.BeginAddress!=previewMusicWrapper.size)continue;
   if(gamecode::match(base+f.BeginAddress,previewMusicWrapper)){if(wrapper){log("STAGE VIDEO music pattern ambiguous");return;}wrapper=base+f.BeginAddress;}
  }
  if(!wrapper){log("STAGE VIDEO music pattern unavailable");return;}
  int32_t displacement=0;memcpy(&displacement,wrapper+0x5a,4);auto target=wrapper+0x5e+displacement;
  if(target<base||target+previewMusicNative.size>base+nt->OptionalHeader.SizeOfImage||!gamecode::match(target,previewMusicNative)){log("STAGE VIDEO music target mismatch");return;}
  memcpy(&displacement,wrapper+0x42,4);cell=reinterpret_cast<uintptr_t>(wrapper+0x46+displacement);
  if(cell<reinterpret_cast<uintptr_t>(base)||cell+8>reinterpret_cast<uintptr_t>(base)+nt->OptionalHeader.SizeOfImage){cell=0;return;}
  setter=reinterpret_cast<SetVolume>(target);log("STAGE VIDEO music-only control ready");
 }
 if(!setter)return;
 uintptr_t object=0;float current=0;
 if(!read(cell,object)||!object||!read(object+0x12c,current)||!(current>=0&&current<=1))return;
 if(playing&&!ducked){original=current;applied=original*factor;duckObject=object;setter(reinterpret_cast<void*>(object),0,applied);ducked=true;log("STAGE VIDEO music lowered");}
 if(!playing&&ducked){if(object==duckObject&&abs(current-applied)<.0001f)setter(reinterpret_cast<void*>(object),0,original);ducked=false;log("STAGE VIDEO music restored");}
}

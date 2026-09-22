#pragma once
#include "preview_music.h"
// Called under the loader's existing UI mutex. The helper never writes here.
static void publishStageVideo() {
 static HANDLE mapping=nullptr;static StageVideoShared* shared=nullptr;
 if(!shared) {
  wchar_t name[100];stageVideoMapName(name,100,GetCurrentProcessId());
  mapping=CreateFileMappingW(INVALID_HANDLE_VALUE,nullptr,PAGE_READWRITE,0,sizeof(StageVideoShared),name);
  if(mapping)shared=static_cast<StageVideoShared*>(MapViewOfFile(mapping,FILE_MAP_WRITE,0,0,sizeof(StageVideoShared)));
  if(!shared)return;
 }
 StageVideoFrame frame;frame.tick=GetTickCount64();
 if(stageScreen&&active&&screen==3&&!dialog&&captionLayout) {
  auto layout=reinterpret_cast<uintptr_t>(layoutObject(captionLayout,0,0xd0805c2d,0));
  auto pane=paneNamed(layout,"stage_dummy"),label=paneNamed(layout,"text_stage_dummy");
  uintptr_t matrix=0;float m[16]{};short size[2]{};unsigned char anchor=0,alpha=255;
  if(pane&&label&&read(pane+0xe0,matrix)&&read(matrix,m)&&read(pane+0xf0,size)&&read(pane+0x10c,anchor)&&read(label+0x113,alpha)) {
   frame.width=abs(m[0])*size[0];frame.height=abs(m[5])*size[1];
   frame.x=m[12];frame.y=m[13];
   if((anchor>>4)==1)frame.x-=frame.width*.5f;else if((anchor>>4)==2)frame.x-=frame.width;
   frame.nameAlpha=alpha;
   if(stageCaption.rfind("Slot: S",0)==0||stageCaption=="Slot: Random Vanilla Stage/Modded Stage") {
    auto code=stageCaption.rfind("Slot: S",0)==0?stageCaption.substr(6,8):std::string("Random");strncpy_s(frame.slot,code.c_str(),_TRUNCATE);
    frame.active=frame.width>0&&frame.height>0;
   }
  }
 }
 InterlockedIncrement(&shared->sequence);shared->frame=frame;MemoryBarrier();InterlockedIncrement(&shared->sequence);
 auto audioTick=static_cast<ULONGLONG>(InterlockedCompareExchange64(&shared->audioTick,0,0));
 previewMusic(frame.active&&InterlockedCompareExchange(&shared->audioPlaying,0,0)&&frame.tick-audioTick<500);
 static bool helperAttempted=false;
 if(frame.active&&!helperAttempted) {
  helperAttempted=true;
  auto exe=gameRoot+L"REDELBE_LR\\StageVideoTest\\StageVideoPreviewTest.exe";
  auto command=L"\""+exe+L"\" "+std::to_wstring(GetCurrentProcessId())+L" \""+gameRoot+L"REDELBE_LR\\StageVidPreviews\"";
  STARTUPINFOW startup{};startup.cb=sizeof(startup);startup.dwFlags=STARTF_USESHOWWINDOW;startup.wShowWindow=SW_HIDE;
  PROCESS_INFORMATION process{};
  if(CreateProcessW(exe.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,gameRoot.c_str(),&startup,&process)) {
   CloseHandle(process.hThread);CloseHandle(process.hProcess);log("STAGE VIDEO helper started");
  } else log("STAGE VIDEO helper launch failed error="+std::to_string(GetLastError()));
 }
}

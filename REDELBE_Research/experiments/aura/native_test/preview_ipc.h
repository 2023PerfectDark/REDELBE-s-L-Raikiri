#pragma once
#include <windows.h>
struct StageVideoFrame {
 DWORD version=1;
 DWORD active=0;
 ULONGLONG tick=0;
 char slot[24]{};
 float x=0,y=0,width=0,height=0;
 DWORD nameAlpha=255;
};
struct StageVideoShared { volatile LONG sequence;StageVideoFrame frame;volatile LONG64 audioTick;volatile LONG audioPlaying; };
inline void stageVideoMapName(wchar_t* name,size_t count,DWORD pid) {
 swprintf_s(name,count,L"Local\\REDELBE_LR_StageVideo_%lu",pid);
}

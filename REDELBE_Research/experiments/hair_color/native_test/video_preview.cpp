#define NOMINMAX
#include <windows.h>
#include <tlhelp32.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <wrl/client.h>
#include <algorithm>
#include <string>
#include <vector>
#include <fstream>
#include <filesystem>
#include <random>
#include <mmsystem.h>
#pragma comment(lib,"winmm.lib")
#include "preview_ipc.h"
using Microsoft::WRL::ComPtr;
#pragma comment(lib,"mfplat.lib")
#pragma comment(lib,"mfreadwrite.lib")
#pragma comment(lib,"mfuuid.lib")
#pragma comment(lib,"ole32.lib")
#pragma comment(lib,"user32.lib")
#pragma comment(lib,"gdi32.lib")
#pragma comment(lib,"shell32.lib")
#include <shellapi.h>
#include "preview_audio.h"
static std::wstring randomPreview(const std::wstring& folder,const std::wstring& previous) {
 std::vector<std::wstring> choices;std::error_code error;
 auto directory=std::filesystem::path(folder)/L"Random Vanilla Stage-Modded Stage";
 for(std::filesystem::directory_iterator it(directory,error),end;!error&&it!=end;it.increment(error)) {
  if(!it->is_regular_file(error))continue;
  auto ext=it->path().extension().wstring();
  if(!_wcsicmp(ext.c_str(),L".mp4"))choices.push_back(it->path().wstring());
 }
 if(choices.empty())return {};
 if(choices.size()>1)choices.erase(std::remove(choices.begin(),choices.end(),previous),choices.end());
 static std::mt19937 generator(std::random_device{}());
 return choices[std::uniform_int_distribution<size_t>(0,choices.size()-1)(generator)];
}

struct Video {
 ComPtr<IMFSourceReader> reader;
 UINT32 width=0,height=0;LONG stride=0;
 LONGLONG origin=-1,stamp=0;ULONGLONG start=0;
 LONGLONG lastConverted=-10000000;
 std::vector<BYTE> pixels;bool pending=false;
 bool looped=false;
 void close(){reader.Reset();pixels.clear();pending=false;origin=-1;lastConverted=-10000000;}
 bool open(const std::wstring& file) {
  close();ComPtr<IMFAttributes> attrs;ComPtr<IMFMediaType> type,actual;
  if(FAILED(MFCreateAttributes(&attrs,2)))return false;
  attrs->SetUINT32(MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING,TRUE);
  if(FAILED(MFCreateSourceReaderFromURL(file.c_str(),attrs.Get(),&reader)))return false;
  reader->SetStreamSelection(MF_SOURCE_READER_ALL_STREAMS,FALSE);
  reader->SetStreamSelection(MF_SOURCE_READER_FIRST_VIDEO_STREAM,TRUE);
  MFCreateMediaType(&type);type->SetGUID(MF_MT_MAJOR_TYPE,MFMediaType_Video);type->SetGUID(MF_MT_SUBTYPE,MFVideoFormat_RGB32);
  if(FAILED(reader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM,nullptr,type.Get()))||
     FAILED(reader->GetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM,&actual))||
     FAILED(MFGetAttributeSize(actual.Get(),MF_MT_FRAME_SIZE,&width,&height))||!width||!height||width>3840||height>2160){close();return false;}
  UINT32 rawStride=0;
  if(SUCCEEDED(actual->GetUINT32(MF_MT_DEFAULT_STRIDE,&rawStride)))stride=static_cast<LONG>(rawStride);else stride=static_cast<LONG>(width*4);
  start=GetTickCount64();return true;
 }
 bool frame(ULONGLONG now,bool& updated) {
  updated=false;looped=false;if(!reader)return false;
  if(pending&&now-start<static_cast<ULONGLONG>(std::max<LONGLONG>(0,stamp-origin)/10000))return true;
  if(pending){pending=false;updated=true;return true;}
  DWORD flags=0;ComPtr<IMFSample> sample;
  if(FAILED(reader->ReadSample(MF_SOURCE_READER_FIRST_VIDEO_STREAM,0,nullptr,&flags,&stamp,&sample)))return false;
  if(flags&MF_SOURCE_READERF_CURRENTMEDIATYPECHANGED) {
   ComPtr<IMFMediaType> actual;UINT32 newStride=0;
   if(FAILED(reader->GetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM,&actual)))return false;
   // Keep the requested visible dimensions: the negotiated frame size can
   // include decoder padding (e.g. 1408 rather than 1400 pixels).
   stride=SUCCEEDED(actual->GetUINT32(MF_MT_DEFAULT_STRIDE,&newStride))?static_cast<LONG>(newStride):static_cast<LONG>(width*4);
  }
  if(flags&MF_SOURCE_READERF_ENDOFSTREAM) {
   PROPVARIANT pos{};pos.vt=VT_I8;pos.hVal.QuadPart=0;
   if(FAILED(reader->SetCurrentPosition(GUID_NULL,pos)))return false;
   origin=-1;lastConverted=-10000000;start=now;looped=true;return true;
  }
  if(!sample)return true;
  // Convert/present at most 30 fps; preserve the source timestamps and speed.
  if(stamp-lastConverted<300000)return true;
  lastConverted=stamp;
  ComPtr<IMFMediaBuffer> buffer;if(FAILED(sample->ConvertToContiguousBuffer(&buffer)))return false;
  BYTE* data=nullptr;DWORD length=0;LONG actualStride=stride;
  ComPtr<IMF2DBuffer> imageBuffer;bool locked2D=false;
  if(SUCCEEDED(buffer.As(&imageBuffer))&&SUCCEEDED(imageBuffer->Lock2D(&data,&actualStride)))locked2D=true;
  else if(FAILED(buffer->Lock(&data,nullptr,&length)))return false;
  const size_t pitch=static_cast<size_t>(abs(actualStride));
  bool valid=pitch>=width*4&&(locked2D||length>=pitch*height);
  if(valid) {
   pixels.resize(static_cast<size_t>(width)*height*4);
   for(UINT32 row=0;row<height;++row) {
    const BYTE* src=locked2D?data+static_cast<ptrdiff_t>(row)*actualStride:data+(actualStride<0?height-1-row:row)*pitch;
    BYTE* dst=pixels.data()+static_cast<size_t>(row)*width*4;
    memcpy(dst,src,width*4);
   }
  }
  if(locked2D)imageBuffer->Unlock2D();else buffer->Unlock();if(!valid)return false;
  if(origin<0){origin=stamp;start=now;}
  pending=true;
  if(now-start>=static_cast<ULONGLONG>(std::max<LONGLONG>(0,stamp-origin)/10000)){pending=false;updated=true;}
  return true;
 }
};
static LRESULT CALLBACK windowProc(HWND window,UINT msg,WPARAM w,LPARAM l) {
 if(msg==WM_NCHITTEST)return HTTRANSPARENT;
 if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
 return DefWindowProcW(window,msg,w,l);
}
static bool paint(HWND window,const RECT& bounds,const Video& video,BYTE alpha) {
 int width=bounds.right-bounds.left,height=bounds.bottom-bounds.top;
 if(width<=0||height<=0||width>7680||height>4320||video.pixels.empty())return false;
 struct Surface {
  HDC dc=CreateCompatibleDC(nullptr);HBITMAP bitmap=nullptr;HGDIOBJ old=nullptr;
  void* bits=nullptr;int width=0,height=0;
  ~Surface(){if(bitmap){SelectObject(dc,old);DeleteObject(bitmap);}DeleteDC(dc);}
 };
 static Surface surface;
 HDC screen=GetDC(nullptr),dc=surface.dc;
 BITMAPINFO bi{};bi.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);bi.bmiHeader.biWidth=width;bi.bmiHeader.biHeight=-height;bi.bmiHeader.biPlanes=1;bi.bmiHeader.biBitCount=32;bi.bmiHeader.biCompression=BI_RGB;
 if(surface.width!=width||surface.height!=height) {
  if(surface.bitmap){SelectObject(dc,surface.old);DeleteObject(surface.bitmap);surface.bitmap=nullptr;}
  surface.bitmap=CreateDIBSection(screen,&bi,DIB_RGB_COLORS,&surface.bits,nullptr,0);
  if(!surface.bitmap){surface.width=surface.height=0;ReleaseDC(nullptr,screen);return false;}
  surface.old=SelectObject(dc,surface.bitmap);surface.width=width;surface.height=height;
 }
 BITMAPINFO source=bi;source.bmiHeader.biWidth=video.width;source.bmiHeader.biHeight=-static_cast<LONG>(video.height);
 float fit=std::min(width/float(video.width),height/float(video.height));
 int vw=int(video.width*fit),vh=int(video.height*fit);
 if(vw!=width||vh!=height)PatBlt(dc,0,0,width,height,BLACKNESS);
 SetStretchBltMode(dc,COLORONCOLOR);
 StretchDIBits(dc,(width-vw)/2,(height-vh)/2,vw,vh,0,0,video.width,video.height,video.pixels.data(),&source,DIB_RGB_COLORS,SRCCOPY);
 POINT destination{bounds.left,bounds.top},zero{};SIZE size{width,height};BLENDFUNCTION blend{AC_SRC_OVER,0,alpha,0};
 bool ok=UpdateLayeredWindow(window,screen,&destination,&size,dc,&zero,0,&blend,ULW_ALPHA)!=FALSE;
 ReleaseDC(nullptr,screen);return ok;
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,LPWSTR,int) {
 int argc=0;auto args=CommandLineToArgvW(GetCommandLineW(),&argc);
 DWORD pid=0;std::wstring folder;
 if(argc==3) {pid=wcstoul(args[1],nullptr,10);folder=args[2];}
 else if(argc==1) {
  wchar_t executable[32768]{};GetModuleFileNameW(nullptr,executable,32768);
  auto gamePath=std::filesystem::path(executable).parent_path();
  while(!gamePath.empty()&&!std::filesystem::exists(gamePath/L"DOA6LR.exe")) {
   auto parent=gamePath.parent_path();if(parent==gamePath){gamePath.clear();break;}gamePath=parent;
  }
  if(gamePath.empty()) {LocalFree(args);MessageBoxW(nullptr,L"Keep this helper inside your DOA6LR game folder. Start the game and open Stage Select to use video previews.",L"REDELBE LR video preview",MB_OK);return 1;}
  auto data=gamePath/L"REDELBE's Last Raikiri"/L"REDELBE LR";
  if(!std::filesystem::exists(data))data=gamePath/L"REDELBE_LR";
  folder=(data/L"StageVidPreviews").wstring();
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);
  if(snapshot!=INVALID_HANDLE_VALUE) {
   PROCESSENTRY32W entry{};entry.dwSize=sizeof(entry);
   if(Process32FirstW(snapshot,&entry)) do {
    if(_wcsicmp(entry.szExeFile,L"DOA6LR.exe"))continue;
    HANDLE candidate=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,entry.th32ProcessID);
    if(candidate) {
     wchar_t path[32768]{};DWORD size=32768;std::error_code ec;
     if(QueryFullProcessImageNameW(candidate,0,path,&size)&&std::filesystem::equivalent(path,gamePath/L"DOA6LR.exe",ec))pid=entry.th32ProcessID;
     CloseHandle(candidate);
    }
   } while(!pid&&Process32NextW(snapshot,&entry));
   CloseHandle(snapshot);
  }
  if(!pid){LocalFree(args);MessageBoxW(nullptr,L"Start this copy of DOA6LR first, then open Stage Select. The loader normally starts video previews automatically.",L"REDELBE LR video preview",MB_OK);return 2;}
 } else {LocalFree(args);return 1;}
 LocalFree(args);
 std::wstring ini=folder.substr(0,folder.find_last_of(L"\\/"))+L"\\REDELBE.ini";
 wchar_t audioSetting[32]{};GetPrivateProfileStringW(L"StageVideoPreviews",L"audio_enabled",L"true",audioSetting,32,ini.c_str());
 bool audioEnabled=!_wcsicmp(audioSetting,L"true")||!wcscmp(audioSetting,L"1");
 unsigned audioVolume=std::min(100u,GetPrivateProfileIntW(L"StageVideoPreviews",L"audio_volume",100,ini.c_str()));
 std::ofstream diagnostics(folder+L"\\preview_test.log",std::ios::app);
 auto report=[&](const std::string& message){diagnostics<<GetTickCount64()<<" "<<message<<std::endl;};
 report("helper starting pid="+std::to_string(pid));
 HANDLE game=OpenProcess(SYNCHRONIZE,FALSE,pid);if(!game)return 2;
 wchar_t mapName[100];stageVideoMapName(mapName,100,pid);
 HANDLE singleton=CreateMutexW(nullptr,TRUE,(std::wstring(mapName)+L"_player").c_str());if(GetLastError()==ERROR_ALREADY_EXISTS){CloseHandle(game);CloseHandle(singleton);return 0;}
 if(FAILED(CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED)))return 3;
 if(FAILED(MFStartup(MF_VERSION)))return 4;
 timeBeginPeriod(1);
 SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
 WNDCLASSW wc{};wc.lpfnWndProc=windowProc;wc.hInstance=instance;wc.lpszClassName=L"REDELBEStageVideoTest";RegisterClassW(&wc);
 HWND window=CreateWindowExW(WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,wc.lpszClassName,L"REDELBE stage video test",WS_POPUP,0,0,1,1,nullptr,nullptr,instance,nullptr);
 HANDLE mapping=nullptr;StageVideoShared* shared=nullptr;Video video;PreviewAudio audio;std::string slot;
 ULONGLONG retry=0,fade=0,nameHiddenSince=0,lastPaint=0;bool visible=false;
 std::string lastStatus;
 std::wstring currentVideo,lastRandomVideo;
 StageVideoFrame lastFrame{};bool haveFrame=false;
 while(WaitForSingleObject(game,0)==WAIT_TIMEOUT) {
  MSG msg;while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessageW(&msg);}
  auto now=GetTickCount64();StageVideoFrame frame;bool snapshot=false;
  if(!shared){mapping=OpenFileMappingW(FILE_MAP_READ|FILE_MAP_WRITE,FALSE,mapName);if(mapping)shared=static_cast<StageVideoShared*>(MapViewOfFile(mapping,FILE_MAP_READ|FILE_MAP_WRITE,0,0,sizeof(StageVideoShared)));if(mapping&&!shared){CloseHandle(mapping);mapping=nullptr;}}
  if(shared){LONG a=shared->sequence;MemoryBarrier();frame=shared->frame;MemoryBarrier();snapshot=!(a&1)&&a==shared->sequence&&frame.version==1;}
  // A concurrent publication is not a screen change. Retain the last stable
  // snapshot until its normal freshness timeout instead of restarting playback.
  if(snapshot){lastFrame=frame;haveFrame=true;}
  else if(haveFrame){frame=lastFrame;snapshot=true;}
  HWND foreground=GetForegroundWindow();DWORD owner=0;GetWindowThreadProcessId(foreground,&owner);
  bool active=snapshot&&frame.active&&now-frame.tick<500&&owner==pid;
  std::string status="snapshot="+std::to_string(snapshot)+" stage="+std::to_string(frame.active)+" foreground="+std::to_string(owner==pid)+" fresh="+std::to_string(now-frame.tick<500)+" name="+std::to_string(frame.nameAlpha);
  if(status!=lastStatus){report(status);lastStatus=status;}
  if(!active||slot!=frame.slot) {
   ShowWindow(window,SW_HIDE);visible=false;fade=0;nameHiddenSince=0;audio.close();video.close();retry=0;slot=active?frame.slot:"";
  }
  if(!active){if(shared)InterlockedExchange(&shared->audioPlaying,0);Sleep(16);continue;}
  if(frame.nameAlpha!=0) {
   if(visible)ShowWindow(window,SW_HIDE);
   visible=false;fade=0;nameHiddenSince=0;audio.close();video.close();retry=0;if(shared)InterlockedExchange(&shared->audioPlaying,0);Sleep(16);continue;
  }
  // Zero can appear briefly before the native title entrance starts. Require
  // a stable fully hidden title, not merely its first zero-opacity frame.
  if(!nameHiddenSince)nameHiddenSince=now;
  if(now-nameHiddenSince<250){if(shared)InterlockedExchange(&shared->audioPlaying,0);Sleep(8);continue;}
  if(!video.reader&&now>=retry) {
   std::wstring code(slot.begin(),slot.end());retry=now+1000;
   currentVideo=slot=="Random"?randomPreview(folder,lastRandomVideo):folder+L"\\"+code+L".mp4";
   if(currentVideo.empty()||!video.open(currentVideo)){report("open failed "+slot);Sleep(16);continue;}
   if(slot=="Random")lastRandomVideo=currentVideo;
   report("opened "+slot+" size="+std::to_string(video.width)+"x"+std::to_string(video.height));
   if(audioEnabled)report(audio.open(currentVideo,audioVolume)?"audio ready":"no playable audio track");
  }
  bool updated=false;
  if(video.reader&&!video.frame(now,updated)){report("decode failed");audio.close();video.close();ShowWindow(window,SW_HIDE);visible=false;fade=0;retry=now+1000;}
  if(video.looped&&slot=="Random") {
   audio.close();video.close();ShowWindow(window,SW_HIDE);visible=false;fade=0;retry=0;
   if(shared)InterlockedExchange(&shared->audioPlaying,0);
   continue;
  }
  if(video.looped)audio.rewind();
  // Fade independently of decoder cadence, including static/low-frame-rate
  // clips. Never leave the overlay parked on its initial transparent frame.
  now=GetTickCount64();
  if(!video.pixels.empty()&&(updated||!fade||(now-fade<550&&now-lastPaint>=16))) {
   if(!fade)fade=now;
   RECT client{};POINT origin{};GetClientRect(foreground,&client);ClientToScreen(foreground,&origin);
   float scale=std::min(client.right/1920.f,client.bottom/1080.f);
   int x=origin.x+int((client.right-1920*scale)*.5f+(960+frame.x)*scale);
   int y=origin.y+int((client.bottom-1080*scale)*.5f+(540-frame.y-frame.height*.5f)*scale);
   RECT bounds{x,y,x+int(frame.width*scale),y+int(frame.height*scale)};
   BYTE alpha=static_cast<BYTE>(std::min<ULONGLONG>(255,(now-fade)*255/500));
   lastPaint=now;
   if(paint(window,bounds,video,alpha)) {
    // The game can raise its window during the native title transition.
    SetWindowPos(window,HWND_TOPMOST,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW);
    if(alpha&&!visible){visible=true;report("overlay visible at "+std::to_string(x)+","+std::to_string(y));}
   } else {
    if(visible)report("overlay paint failed error="+std::to_string(GetLastError()));
    visible=false;
   }
  }
  bool audible=visible&&audio.pump();
  if(shared){InterlockedExchange(&shared->audioPlaying,audible?1:0);InterlockedExchange64(&shared->audioTick,static_cast<LONG64>(now));}
  Sleep(1);
 }
 audio.close();video.close();DestroyWindow(window);if(shared)UnmapViewOfFile(shared);if(mapping)CloseHandle(mapping);CloseHandle(game);CloseHandle(singleton);timeEndPeriod(1);MFShutdown();CoUninitialize();return 0;
}

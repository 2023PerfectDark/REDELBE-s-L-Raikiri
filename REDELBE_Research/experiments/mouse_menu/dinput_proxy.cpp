// Minimal DirectInput proxy: load only our adjacent loader, outside DllMain.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <unknwn.h>
#include <string>
#include <mutex>
static HMODULE self,systemInput;
static std::once_flag once;
static DWORD WINAPI initializeLoader(void*) {
 wchar_t path[32768];DWORD n=GetModuleFileNameW(nullptr,path,32768);std::wstring exe(path,n);
 if(_wcsicmp(exe.substr(exe.find_last_of(L"\\")+1).c_str(),L"DOA6LR.exe"))return 0;
#ifdef REDELBE_COMBINED
 auto init=reinterpret_cast<void(*)()>(GetProcAddress(self,"InitializeASIWhenReady"));if(init)init();
#else
 // An existing ASI loader owns initialization if it already loaded the module.
 if(GetModuleHandleW(L"REDELBE_LR.asi"))return 0;
 n=GetModuleFileNameW(self,path,32768);std::wstring folder(path,n);folder.resize(folder.find_last_of(L"\\"));
 auto loader=LoadLibraryW((folder+L"\\REDELBE_LR.asi").c_str());
 if(loader){auto init=reinterpret_cast<void(*)()>(GetProcAddress(loader,"InitializeASIWhenReady"));if(init)init();}
#endif
 return 0;
}
static FARPROC proc(const char* name) {
 std::call_once(once,[]{
  wchar_t path[32768];UINT n=GetSystemDirectoryW(path,32768);
  if(!n||n>=32768)return;
  systemInput=LoadLibraryExW((std::wstring(path,n)+L"\\dinput8.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
 });
 return systemInput?GetProcAddress(systemInput,name):nullptr;
}
extern "C" HRESULT WINAPI DirectInput8Create(HINSTANCE h,DWORD version,REFIID iid,LPVOID* out,LPUNKNOWN outer) {
 auto fn=reinterpret_cast<HRESULT(WINAPI*)(HINSTANCE,DWORD,REFIID,LPVOID*,LPUNKNOWN)>(proc("DirectInput8Create"));
 return fn?fn(h,version,iid,out,outer):E_FAIL;
}
extern "C" HRESULT WINAPI DllCanUnloadNow(){auto fn=reinterpret_cast<HRESULT(WINAPI*)()>(proc("DllCanUnloadNow"));return fn?fn():S_FALSE;}
extern "C" HRESULT WINAPI DllGetClassObject(REFCLSID cls,REFIID iid,LPVOID* out){auto fn=reinterpret_cast<HRESULT(WINAPI*)(REFCLSID,REFIID,LPVOID*)>(proc("DllGetClassObject"));return fn?fn(cls,iid,out):E_FAIL;}
extern "C" HRESULT WINAPI DllRegisterServer(){auto fn=reinterpret_cast<HRESULT(WINAPI*)()>(proc("DllRegisterServer"));return fn?fn():E_FAIL;}
extern "C" HRESULT WINAPI DllUnregisterServer(){auto fn=reinterpret_cast<HRESULT(WINAPI*)()>(proc("DllUnregisterServer"));return fn?fn():E_FAIL;}
void StartREDELBEProxy(HINSTANCE h){self=h;auto worker=CreateThread(nullptr,0,initializeLoader,nullptr,0,nullptr);if(worker)CloseHandle(worker);}
#ifndef REDELBE_COMBINED
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,LPVOID){
 if(reason==DLL_PROCESS_ATTACH)StartREDELBEProxy(h);
 return TRUE;
}
#endif

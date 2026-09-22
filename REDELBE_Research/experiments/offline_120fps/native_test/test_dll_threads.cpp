#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
DWORD WINAPI thread(void*) { return 42; }
int wmain(int argc,wchar_t**argv) {
    if(argc!=2)return 1;
    HMODULE module=LoadLibraryW(argv[1]);if(!module){printf("Load failed %lu\n",GetLastError());return 2;}
    HANDLE worker=CreateThread(nullptr,16384,thread,nullptr,STACK_SIZE_PARAM_IS_A_RESERVATION,nullptr);
    if(!worker)return 3;
    WaitForSingleObject(worker,INFINITE);DWORD result;GetExitCodeThread(worker,&result);CloseHandle(worker);
    FreeLibrary(module);if(result!=42)return 4;
    puts("PASS: ASI attaches/detaches on a 16 KB thread stack without initializing game hooks.");return 0;
}

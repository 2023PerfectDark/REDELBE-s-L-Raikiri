// Launch the adjacent official game with its own directory as working directory.
// Steam supplies its normal launch environment; no game or Steam checks are patched.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>
#include <fstream>
#include <iterator>

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    wchar_t own[32768];
    DWORD length = GetModuleFileNameW(nullptr, own, 32768);
    if (!length || length >= 32768) return 1;
    std::wstring folder(own, length);
    folder.resize(folder.find_last_of(L"\\"));
    // Keep one preparation/game lifetime per backup launcher instance.
    unsigned long long folderId=14695981039346656037ull;
    for(wchar_t c:folder){folderId^=static_cast<unsigned short>(towlower(c));folderId*=1099511628211ull;}
    std::wstring mutexName=L"Local\\REDELBE_LR_"+std::to_wstring(folderId);
    HANDLE lifetime=CreateMutexW(nullptr,FALSE,mutexName.c_str());
    if(!lifetime)return 5;
    if(GetLastError()==ERROR_ALREADY_EXISTS) {
        CloseHandle(lifetime);
        MessageBoxW(nullptr,L"This game copy is already starting or running. Return to its game window instead of starting another copy.",L"REDELBE LR",MB_OK|MB_ICONINFORMATION);return 0;
    }
    std::wstring sync=folder+L"\\REDELBE_LR_Sync.exe";
    if(GetFileAttributesW(sync.c_str())!=INVALID_FILE_ATTRIBUTES) {
        std::wstring syncCommand=L"\""+sync+L"\" sync \""+folder+L"\"";
        STARTUPINFOW prep{};prep.cb=sizeof(prep);PROCESS_INFORMATION worker{};
        if(!CreateProcessW(sync.c_str(),syncCommand.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,
                           nullptr,folder.c_str(),&prep,&worker)) {
            MessageBoxW(nullptr,L"Could not run REDELBE/Kashira synchronization.",L"REDELBE LR",MB_OK|MB_ICONERROR);return 3;
        }
        CloseHandle(worker.hThread);
        HWND status=CreateWindowExW(WS_EX_TOPMOST,L"STATIC",L"Checking mods and synchronizing REDELBE / Kashira...\nThe game will start automatically when ready.",WS_CAPTION|WS_POPUP|WS_VISIBLE|SS_CENTER, CW_USEDEFAULT,CW_USEDEFAULT,520,100,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);
        while(WaitForSingleObject(worker.hProcess,50)==WAIT_TIMEOUT){
            MSG msg{};while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessageW(&msg);}
        }
        if(status)DestroyWindow(status);
        DWORD code=1;GetExitCodeProcess(worker.hProcess,&code);CloseHandle(worker.hProcess);
        if(code) {
            std::ifstream detailFile(folder+L"\\REDELBE_LR\\bridge_last_error.txt");
            std::string detail((std::istreambuf_iterator<char>(detailFile)),std::istreambuf_iterator<char>());
            int n=MultiByteToWideChar(CP_UTF8,0,detail.data(),static_cast<int>(detail.size()),nullptr,0);
            std::wstring why(n,L'\0');
            if(n)MultiByteToWideChar(CP_UTF8,0,detail.data(),static_cast<int>(detail.size()),why.data(),n);
            if(why.empty())why=L"Run Sync REDELBE Layer2.cmd in this folder for details.";
            std::wstring message=L"Kashira/Layer2 preparation failed:\n\n"+why+L"\n\nThe game was not started.";
            MessageBoxW(nullptr,message.c_str(),L"REDELBE LR",MB_OK|MB_ICONERROR);return 4;
        }
    }
    else {MessageBoxW(nullptr,L"REDELBE_LR_Sync.exe is missing. Restore it beside this launcher before starting.",L"REDELBE LR",MB_OK|MB_ICONERROR);return 3;}
    std::wstring game = folder + L"\\DOA6LR.exe";
    std::wstring command = L"\"" + game + L"\"";
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION child{};
    if (!CreateProcessW(game.c_str(), command.data(), nullptr, nullptr, FALSE, 0,
                        nullptr, folder.c_str(), &startup, &child)) {
        MessageBoxW(nullptr, L"Could not start the adjacent DOA6LR.exe.",
                    L"REDELBE LR test launcher", MB_OK | MB_ICONERROR);
        return 2;
    }
    CloseHandle(child.hThread);
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD result = 1;
    GetExitCodeProcess(child.hProcess, &result);
    CloseHandle(child.hProcess);
    return static_cast<int>(result);
}

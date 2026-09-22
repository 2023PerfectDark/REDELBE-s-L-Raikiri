// Experimental Last Round resource overlay with fingerprinted LR-native Layer2 hooks.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <intrin.h>
#include <string>
#include <map>
#include <vector>
#include <fstream>
#include <mutex>
#include <algorithm>
#include <cwctype>
#include <psapi.h>
#include "user_config.h"
#pragma comment(lib, "bcrypt.lib")

static decltype(&CreateFileW) realW = CreateFileW;
static decltype(&CreateFileA) realA = CreateFileA;
static decltype(&K32EnumProcessModulesEx) realModules = K32EnumProcessModulesEx;
static decltype(&ExitProcess) realExit = ExitProcess;
static decltype(&TerminateProcess) realTerminate = TerminateProcess;
static std::wstring gameRoot, workRoot;
static std::map<std::wstring, std::wstring> redirects;
static HANDLE logFile = INVALID_HANDLE_VALUE;
static std::mutex logMutex;
static unsigned logCount = 0;
static HMODULE self;
static std::once_flag initialized;
static std::recursive_mutex initializationMutex;
static bool startupAttempted=false;

static std::string utf8(const std::wstring& s) {
    int n = WideCharToMultiByte(CP_UTF8, 0, s.data(), (int)s.size(), nullptr, 0, nullptr, nullptr);
    std::string r(n, 0);
    if (n) WideCharToMultiByte(CP_UTF8, 0, s.data(), (int)s.size(), &r[0], n, nullptr, nullptr);
    return r;
}
static std::wstring wide(const std::string& s, UINT cp = CP_UTF8) {
    int n = MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, s.data(), (int)s.size(), nullptr, 0);
    std::wstring r(n, 0);
    if (n) MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, s.data(), (int)s.size(), &r[0], n);
    return r;
}
static std::wstring lower(std::wstring s) {
    for (auto& c : s) c = c == L'/' ? L'\\' : (wchar_t)towlower(c);
    return s;
}
static std::wstring full(const wchar_t* p) {
    wchar_t buf[32768]; DWORD n = GetFullPathNameW(p, 32768, buf, nullptr);
    return n && n < 32768 ? lower(std::wstring(buf, n)) : L"";
}
static void log(const std::string& s) {
    if (logFile == INVALID_HANDLE_VALUE) return;
    DWORD error = GetLastError();
    std::lock_guard<std::mutex> lock(logMutex);
    std::string line = std::to_string(GetTickCount64()) + " " + s + "\r\n";
    DWORD wrote; WriteFile(logFile, line.data(), (DWORD)line.size(), &wrote, nullptr);
    SetLastError(error);
}
static bool sha256(const std::wstring& path, std::string& result) {
    HANDLE f = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, 0, nullptr);
    if (f == INVALID_HANDLE_VALUE) return false;
    BCRYPT_ALG_HANDLE alg = nullptr; BCRYPT_HASH_HANDLE hash = nullptr;
    bool ok = BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0;
    if (ok) ok = BCryptCreateHash(alg, &hash, nullptr, 0, nullptr, 0, 0) >= 0;
    std::vector<UCHAR> data(1024*1024); DWORD n = 0;
    while (ok) {
        if (!ReadFile(f, data.data(), (DWORD)data.size(), &n, nullptr)) { ok = false; break; }
        if (!n) break;
        ok = BCryptHashData(hash, data.data(), n, 0) >= 0;
    }
    UCHAR digest[32];
    if (ok) ok = BCryptFinishHash(hash, digest, sizeof(digest), 0) >= 0;
    if (hash) BCryptDestroyHash(hash);
    if (alg) BCryptCloseAlgorithmProvider(alg, 0);
    CloseHandle(f);
    if (ok) { char h[3]; for (auto c : digest) { sprintf_s(h, "%02x", c); result += h; } }
    return ok;
}
#include <xinput.h>
#include "ai_versus_state.h"
#include "pattern_parts_state.h"
#include "preview_ipc.h"
#include "layer2_runtime.h"
#include "ai_versus_hook.h"
#include "pattern_parts_hook.h"
#include "break_blow.h"

static std::wstring selectPath(const wchar_t* path, DWORD access, DWORD disposition, void* caller) {
    if (!path || disposition != OPEN_EXISTING || (access & (GENERIC_WRITE|GENERIC_ALL|FILE_WRITE_DATA|FILE_APPEND_DATA|DELETE))) return L"";
    auto absolute = full(path);
    if (absolute.compare(0, gameRoot.size(), gameRoot) != 0) return L"";
    auto rel = absolute.substr(gameRoot.size());
    bool resource = rel.find(L"fdata_package\\") == 0 || rel.find(L"archive\\") == 0;
    bool loose=rel.find(L"fdata_package\\data\\")==0;
    if (resource && userconfig::current.flag("Debug",loose?"log_external":"log_internal")) {
        bool report = false;
        { std::lock_guard<std::mutex> lock(logMutex); report = logCount++ < 4000; }
        if (report) {
            char addr[40]; sprintf_s(addr, "%llx", (unsigned long long)((char*)caller-(char*)GetModuleHandleW(nullptr)));
            log("OPEN " + utf8(rel) + " caller_rva=" + addr);
        }
    }
    auto layer2Path = l2::select(absolute);
    if (!layer2Path.empty()) return layer2Path;
    auto it = redirects.find(absolute);
    if (it == redirects.end()) return L"";
    if(userconfig::current.flag("Debug","log_virtual"))log("REDIRECT " + utf8(rel) + " -> " + utf8(it->second));
    return it->second;
}
static HANDLE WINAPI hookW(LPCWSTR path, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    DWORD error = GetLastError(); std::wstring target;
    try { target = selectPath(path, a, c, _ReturnAddress()); } catch (...) {}
    SetLastError(error);
    return realW(target.empty() ? path : target.c_str(), a, s, sa, c, f, t);
}
static HANDLE WINAPI hookA(LPCSTR path, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    DWORD error = GetLastError(); std::wstring target;
    try { if (path) target = selectPath(wide(path, AreFileApisANSI() ? CP_ACP : CP_OEMCP).c_str(), a, c, _ReturnAddress()); } catch (...) {}
    SetLastError(error);
    return target.empty() ? realA(path, a, s, sa, c, f, t) : realW(target.c_str(), a, s, sa, c, f, t);
}
// REDELBE's original startup compatibility hook omits its own module from the
// game's module query. Apply only to this game's query of its own process and
// bound reads by the caller's actual buffer capacity (unlike the old loop).
static BOOL WINAPI hookModules(HANDLE process, HMODULE* modules, DWORD bytes, LPDWORD needed, DWORD filter) {
    BOOL ok=realModules(process,modules,bytes,needed,filter);
    DWORD error=GetLastError();
    if(ok && needed && modules && GetProcessId(process)==GetCurrentProcessId()) {
        size_t count=std::min(bytes,*needed)/sizeof(HMODULE);
        for(size_t i=0;i<count;++i) {
            if(modules[i]==self) {
                memmove(modules+i,modules+i+1,(count-i-1)*sizeof(HMODULE));
                *needed-=sizeof(HMODULE);
                log("Startup compatibility: omitted only REDELBE_LR from game module query");
                break;
            }
        }
    }
    SetLastError(error);return ok;
}
struct Slot { void** cell; void* original; void* hook; };
static void WINAPI traceExit(UINT code) {
    log("EXIT code="+std::to_string(code)+" caller_rva="+std::to_string(reinterpret_cast<uintptr_t>(_ReturnAddress())-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))));
    realExit(code);
}
static BOOL WINAPI traceTerminate(HANDLE process,UINT code) {
    log("TERMINATE code="+std::to_string(code)+" caller_rva="+std::to_string(reinterpret_cast<uintptr_t>(_ReturnAddress())-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))));
    return realTerminate(process,code);
}
static bool installImports() {
    auto base = (BYTE*)GetModuleHandleW(nullptr);
    auto dos = (IMAGE_DOS_HEADER*)base;
    auto nt = (IMAGE_NT_HEADERS64*)(base + dos->e_lfanew);
    auto rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (!rva) return false;
    std::vector<Slot> slots;
    for (auto d = (IMAGE_IMPORT_DESCRIPTOR*)(base+rva); d->Name; ++d) {
        if (_stricmp((char*)base+d->Name, "kernel32.dll") || !d->OriginalFirstThunk) continue;
        auto names = (IMAGE_THUNK_DATA64*)(base+d->OriginalFirstThunk);
        auto addr = (IMAGE_THUNK_DATA64*)(base+d->FirstThunk);
        for (; names->u1.AddressOfData; ++names, ++addr) {
            if (IMAGE_SNAP_BY_ORDINAL64(names->u1.Ordinal)) continue;
            auto name = (char*)((IMAGE_IMPORT_BY_NAME*)(base+names->u1.AddressOfData))->Name;
            void* replacement = nullptr;
            if (!strcmp(name,"CreateFileW")) { realW = (decltype(realW))addr->u1.Function; replacement = (void*)hookW; }
            if (!strcmp(name,"CreateFileA")) { realA = (decltype(realA))addr->u1.Function; replacement = (void*)hookA; }
            if (!strcmp(name,"K32EnumProcessModulesEx")) { realModules = (decltype(realModules))addr->u1.Function; replacement = (void*)hookModules; }
            if (!strcmp(name,"ExitProcess")) { realExit = (decltype(realExit))addr->u1.Function; replacement = (void*)traceExit; }
            if (!strcmp(name,"TerminateProcess")) { realTerminate = (decltype(realTerminate))addr->u1.Function; replacement = (void*)traceTerminate; }
            if (replacement) slots.push_back({(void**)&addr->u1.Function, (void*)addr->u1.Function, replacement});
        }
    }
    if (slots.empty()) return false;
    std::vector<DWORD> protections;
    for (auto& slot : slots) {
        DWORD old;
        if (!VirtualProtect(slot.cell, sizeof(void*), PAGE_READWRITE, &old)) {
            for (size_t i=protections.size();i-->0;) { DWORD temp; VirtualProtect(slots[i].cell,sizeof(void*),protections[i],&temp); }
            return false;
        }
        protections.push_back(old);
    }
    for (auto& slot : slots) InterlockedExchangePointer(slot.cell, slot.hook);
    // Reverse order matters if slots share one page.
    for (size_t i=slots.size();i-->0;) { DWORD temp; VirtualProtect(slots[i].cell,sizeof(void*),protections[i],&temp); }
    log("Installed resource/startup import hooks: " + std::to_string(slots.size()));
    return true;
}
static void start() {
    wchar_t exe[32768], dll[32768];
    GetModuleFileNameW(nullptr,exe,32768); GetModuleFileNameW(self,dll,32768);
    std::wstring exePath(exe), dllPath(dll);
    if (_wcsicmp(exePath.substr(exePath.find_last_of(L"\\")+1).c_str(),L"DOA6LR.exe")) return;
    gameRoot=full(exe); gameRoot.resize(gameRoot.find_last_of(L"\\")+1);
    workRoot=dllPath.substr(0,dllPath.find_last_of(L"\\")+1)+L"REDELBE_LR\\";
    CreateDirectoryW(workRoot.c_str(),nullptr);
    logFile=CreateFileW((workRoot+L"loader.log").c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_ALWAYS,0,nullptr);
    log("REDELBE LR 0.3 RC4; validated runtime patterns and portable Kashira bridge");
    {
        std::ifstream ini(gameRoot+L"REDELBE_LR\\REDELBE.ini");
        if(ini)userconfig::current.parse(ini);
        log(std::string("SETTINGS ")+(ini.is_open()?"loaded REDELBE_LR/REDELBE.ini":"defaults (INI absent)"));
        for(const auto& message:userconfig::current.diagnostics)log("SETTINGS "+message);
        log(std::string("SETTINGS roster_transitions=")+(userconfig::current.flag("UI","character_roster_transitions")?"true":"false"));
    }
    std::string hash;
    if (!sha256(exePath,hash)) { log("DISABLED: executable hash failed"); return; }
    log("Executable SHA256 " + hash);
    // Validate runtime function patterns before installing any game hooks.
    // Kashira bridge publishes complete generations with an atomic pointer swap.
    // Keep loader.log at the normal root; all package-relative tables use the generation.
    {
        std::ifstream active(workRoot+L"active_package.txt");std::string selected;
        if(active&&std::getline(active,selected)) {
            if(!selected.empty()&&selected.back()=='\r')selected.pop_back();
            auto candidate=full((workRoot+wide(selected)).c_str());
            auto allowed=lower(workRoot+L"sets\\");
            DWORD attrs=GetFileAttributesW(candidate.c_str());
            if(candidate.compare(0,allowed.size(),allowed)||attrs==INVALID_FILE_ATTRIBUTES||!(attrs&FILE_ATTRIBUTE_DIRECTORY)) {
                log("DISABLED: invalid active package");return;
            }
            workRoot=candidate+L"\\";
            log("KASHIRA active package "+selected);
        }
    }
    // Optional UTF-8 TSV: game-relative input<TAB>REDELBE_LR-relative output.
    std::ifstream input(workRoot+L"redirects.tsv"); std::string line;
    while (std::getline(input,line)) {
        if (!line.empty() && line.back()=='\r') line.pop_back();
        if (line.empty() || line[0]=='#') continue;
        auto tab=line.find('\t'); if(tab==std::string::npos) {log("DISABLED: invalid redirect table");return;}
        auto from=full((gameRoot+wide(line.substr(0,tab))).c_str());
        auto to=full((workRoot+wide(line.substr(tab+1))).c_str());
        if(from.compare(0,gameRoot.size(),gameRoot) || to.compare(0,lower(workRoot).size(),lower(workRoot)) || GetFileAttributesW(to.c_str())==INVALID_FILE_ATTRIBUTES) {log("DISABLED: invalid redirect path");return;}
        auto rel=from.substr(gameRoot.size());
        if (rel.find(L"fdata_package\\")!=0) {log("DISABLED: redirects limited to fdata_package");return;}
        if (!redirects.emplace(from,to).second) {log("DISABLED: duplicate redirect");return;}
    }
    if (!redirects.empty()) {
        std::ifstream checks(workRoot+L"baselines.tsv"); unsigned count=0;
        if (!checks) {log("DISABLED: missing baseline fingerprints");return;}
        while (std::getline(checks,line)) {
            if (!line.empty() && line.back()=='\r') line.pop_back();
            if (line.empty()) continue;
            auto tab=line.find('\t');
            if(tab==std::string::npos) {log("DISABLED: invalid baseline table");return;}
            auto path=full((gameRoot+wide(line.substr(0,tab))).c_str());
            std::string digest;
            if(path.compare(0,gameRoot.size(),gameRoot) || !sha256(path,digest) || digest!=line.substr(tab+1)) {log("DISABLED: archive fingerprint changed");return;}
            ++count;
        }
        if (!count) {log("DISABLED: empty baseline table");return;}
        log("Verified archive fingerprints: " + std::to_string(count));
    }
    log("Prepared redirects: " + std::to_string(redirects.size()));
    l2::loadCatalog();
    l2::install();
    try {aivsai::install();}catch(const std::exception& e){log(std::string("AI VS AI unavailable: ")+e.what());}
    try {patternparts::install();}catch(const std::exception& e){log(std::string("PATTERN PARTS unavailable: ")+e.what());}
    if(userconfig::current.flag("Uncensorship","uncensor_loli_blow")) {
        try {
            auto base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
            auto branch=breakblow::resolve(base);const BYTE jump=0xeb;
            l2::write(branch,&jump,1);
            log("BREAK BLOW restriction bypass enabled; validated branch RVA="+std::to_string(branch-base));
        } catch(const std::exception& e) {log(std::string("BREAK BLOW patch skipped: ")+e.what());}
    } else log("BREAK BLOW restriction bypass disabled by INI");
    if (!installImports()) log("DISABLED: import hook preflight failed");
}
extern "C" __declspec(dllexport) void InitializeASI() {
    std::lock_guard<std::recursive_mutex> guard(initializationMutex);startupAttempted=true;
    try { std::call_once(initialized,start); } catch (const std::exception& e) { l2::enabled=false;redirects.clear();log(std::string("DISABLED: ")+e.what()); } catch (...) { l2::enabled=false;redirects.clear();log("DISABLED: initialization exception"); }
}
// The bundled proxy calls this on its worker after the Windows loader lock is
// released. Wait for the protected executable's normal runtime initialization;
// do not patch or decrypt its on-disk image.
extern "C" __declspec(dllexport) void InitializeASIWhenReady() {
    auto deadline=GetTickCount64()+15000;
    while(GetTickCount64()<deadline) {
        std::lock_guard<std::recursive_mutex> guard(initializationMutex);
        if(startupAttempted)return;
        try {
            gamecode::resolve(reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr)));
            InitializeASI();return;
        } catch(const std::exception&) { Sleep(10); }
    }
    InitializeASI(); // Record the unsupported-pattern diagnosis without hooks.
}
#ifdef REDELBE_COMBINED
void StartREDELBEProxy(HINSTANCE);
#endif
BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID) {
    if (reason==DLL_PROCESS_ATTACH) {
#ifdef REDELBE_COMBINED
        StartREDELBEProxy(h);
#endif
        // The proxy also runs in adjacent Kashira tools. Reject attachment there
        // so the editor neither initializes the game hooks nor locks this ASI.
        // Static storage avoids reserving 64 KB on every DLL_THREAD_ATTACH,
        // including game threads created with very small stacks.
        static wchar_t path[32768];
        DWORD size=GetModuleFileNameW(nullptr,path,32768);
        if(!size || size>=32768)return FALSE;
        const wchar_t* name=path;
        for(const wchar_t* p=path;*p;++p)if(*p==L'\\'||*p==L'/')name=p+1;
        if(_wcsicmp(name,L"DOA6LR.exe")) {
#ifdef REDELBE_COMBINED
            return TRUE;
#else
            return FALSE;
#endif
        }
        self=h;
    }
    return TRUE;
}

#pragma once
#include <mmsystem.h>
#pragma comment(lib,"winmm.lib")
namespace wardrobevoice {
static uintptr_t settingsCell=0;
static std::mutex mutex;
static bool wasOpen=false;
static bool infoOpen=false;
template<class T> static bool read(uintptr_t address,T& value){SIZE_T n=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&n)&&n==sizeof(value);}
static void install(){
    auto base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
    auto size=nt->OptionalHeader.SizeOfImage;
    auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
    if(dir.VirtualAddress>=size||dir.Size>size-dir.VirtualAddress)return;
    auto functions=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);
    BYTE* found=nullptr;
    const BYTE pattern[]={0x48,0x83,0xec,0x28,0x48,0x8d,0x0d,0,0,0,0,0xe8,0,0,0,0,0xe8,0,0,0,0,0x8b,0x80,0xcc,0x7e,0x01,0x00,0x48,0x83,0xc4,0x28,0xc3};
    for(unsigned i=0;i<dir.Size/sizeof(RUNTIME_FUNCTION);++i){
        const auto& f=functions[i];if(f.EndAddress>size||f.EndAddress-f.BeginAddress!=sizeof(pattern))continue;
        auto p=base+f.BeginAddress;bool match=true;
        for(unsigned j=0;j<sizeof(pattern);++j){if((j>=7&&j<=10)||(j>=12&&j<=15)||(j>=17&&j<=20))continue;if(p[j]!=pattern[j]){match=false;break;}}
        if(match){if(found){log("WARDROBE VOICE ambiguous language getter; disabled");return;}found=p;}
    }
    if(!found){log("WARDROBE VOICE language getter unavailable; disabled");return;}
    int32_t delta=0;memcpy(&delta,found+17,4);
    auto root=reinterpret_cast<uintptr_t>(found+21)+delta;
    auto begin=reinterpret_cast<uintptr_t>(base);
    if(root<begin||root>begin+size-0x41)return;
    auto p=reinterpret_cast<BYTE*>(root);
    if(memcmp(p+0x35,"\x48\x8b\x05",3)||memcmp(p+0x3c,"\x48\x83\xc4\x38\xc3",5))return;
    memcpy(&delta,p+0x38,4);auto cell=root+0x3c+delta;
    if(cell<begin||cell>begin+size-sizeof(uintptr_t))return;
    settingsCell=cell;log("WARDROBE VOICE language reader ready");
}
static void play(unsigned line){
    if(!settingsCell)return;
    uintptr_t root=0;uint32_t language=0;
    if(!read(settingsCell,root)||!root||!read(root+0x17ecc,language))return;
    const wchar_t* clip=language==0x8ddfa68d?L"nv_us_doa6_kas_":language==0x6eeaefc2?L"nv_doa6_kas_":nullptr;
    if(!clip){log("WARDROBE VOICE unknown dub setting; skipped");return;}
    auto path=gameRoot+L"\\REDELBE_LR\\Audio\\Wardrobe\\"+clip+std::to_wstring(line)+L".wav";
    bool ok=PlaySoundW(path.c_str(),nullptr,SND_FILENAME|SND_ASYNC|SND_NODEFAULT)!=FALSE;
    log(std::string("WARDROBE VOICE ")+(language==0x8ddfa68d?"ENG":"JP")+" line="+std::to_string(line)+(ok?" started":" playback failed"));
}
// All custom Wardrobe panels can share this entry edge, without repeating on hover.
static void sync(bool open){
    std::lock_guard<std::mutex> lock(mutex);
    bool entered=open&&!wasOpen;wasOpen=open;if(entered)play(12);
}
static void animation(uint32_t hash,const char* name){
    if(hash!=0xdf867d44||!name)return;
    std::lock_guard<std::mutex> lock(mutex);
    if(!strcmp(name,"out")){infoOpen=false;return;}
    if(!strcmp(name,"in")&&!infoOpen){infoOpen=true;play(16);}
}
}


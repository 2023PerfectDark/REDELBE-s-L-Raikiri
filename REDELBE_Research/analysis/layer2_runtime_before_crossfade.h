#pragma once
#include <atomic>
#include <sstream>
#include <xinput.h>
#include <intrin.h>
#include "layer2_state.h"
#include "layer2_random_queue.h"
#include "layer2_preview_reload.h"
#include "layer2_slot_names.h"
#include "layer2_model_source.h"
#include "game_patterns.h"

namespace l2 {
struct Mod { std::string name; uint32_t slot; std::map<std::wstring,std::wstring> files; };
static std::vector<Mod> mods;
static std::map<uint32_t,std::vector<size_t>> slots;
static std::map<std::wstring,std::wstring> vanilla;
static Layer2Selection selections, hairSelections;
static std::atomic<int> hairPlayer{-1};
static uint32_t activeHairs[2]{},activeFaces[2]{};
static std::vector<size_t> hairChoices(uint32_t hair,uint32_t face) {
    std::vector<size_t> result;
    for(auto slot:{hair,face}){auto it=slots.find(slot);if(it!=slots.end())result.insert(result.end(),it->second.begin(),it->second.end());}
    return result;
}
static std::recursive_mutex mutex;
static std::atomic<int> routePlayer{0};
static std::atomic<int> selectedPlayer{-1};
static bool enabled=false;
static thread_local bool forceReload=false;
static thread_local uint32_t preservedBody=0;
static thread_local unsigned reloadCacheMisses[4]{};
struct ReloadScope {
    bool previous=forceReload;
    ReloadScope(){forceReload=true;for(auto& count:reloadCacheMisses)count=0;}
    ~ReloadScope(){forceReload=previous;}
};
struct Request { void* object=nullptr; uint32_t player=0,chara=0,costume=0,face=0,hair=0,color=0; int hairColor=-1; };
static Request requests[2];
static Request pendingRequests[2];
static Layer2PreviewReload previewReloads[2];
using ReleaseFn=void(*)(void*,void*);
static ReleaseFn releaseBody;
static uint32_t activeCostumes[2]{};
using RandomFn=void*(*)(void*,void*,void*,uint32_t,bool,bool,uintptr_t,uint8_t);
static RandomFn randomOriginal;
using LoadFn=void*(*)(void*,void*,uint8_t,void*,uint8_t);
static LoadFn loadOriginal;
static Layer2RandomQueue randomQueue;
using RequestFn=uintptr_t(*)(void*,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,int);
using LayoutFn=uintptr_t(*)(void*,uint32_t,const char*,uint32_t);
using CacheFn=bool(*)(void*,uintptr_t,uintptr_t,uintptr_t);
static RequestFn requestOriginal;
static LayoutFn layoutOriginal;
static CacheFn cacheOriginal[4];
using ModelDefaultsFn=void(*)(void*,void*,uint8_t);
static ModelDefaultsFn modelDefaultsOriginal;
static Layer2ModelSources modelSources;
static thread_local bool rebuildModelDefaults=false;
static void* modelDefaultsCacheReturn=nullptr;
static void* modelScaleCacheReturn=nullptr;
static decltype(&XInputGetState) xinputOriginal;
static unsigned layoutLogs=0;
using CaptionFn=void(*)(void*,uintptr_t,uint32_t,uint32_t,uint32_t,const char*);
static CaptionFn setCaption;
static void* captionLayout=nullptr;
static std::string lastCaption;
static std::map<uint32_t,std::string> currentSlotNames;
static std::string hex(uint32_t n) { char b[16];sprintf_s(b,"%08x",n);return b; }
static void showSlotInfo() {
    if(!enabled||!setCaption||!captionLayout)return;
    std::string text;
    {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        bool hairMode=hairPlayer.load()>=0;
        int player=hairMode?hairPlayer.load():selectedPlayer.load();if(player<0||player>1)return;
        const auto& req=requests[player];if(!req.object||!req.costume)return;
        uint32_t shownSlot=hairMode?req.hair:req.costume;
        std::string slot="0x"+hex(shownSlot);
        for(const auto& entry:layer2SlotNames)if(entry.hash==shownSlot){slot=entry.name;break;}
        auto currentName=currentSlotNames.find(shownSlot);if(currentName!=currentSlotNames.end())slot=currentName->second;
        std::string name="Vanilla";
        auto found=slots.find(req.costume);size_t choice=selections.current(player,req.costume);
        if(found!=slots.end()&&choice>0&&choice<=found->second.size())name=mods[found->second[choice-1]].name;
        if(hairMode){auto choices=hairChoices(req.hair,req.face);size_t h=hairSelections.current(player,req.hair,req.face);name=h&&h<=choices.size()?mods[choices[h-1]].name:"Vanilla";}
        text=(hairMode?"Hair: ":"Slot: ")+slot+" Mod: "+name;
    }
    // Same native caption pane and text parameters used by the original REDELBE.
    // The native UTF-8 setter copies/converts the string synchronously.
    setCaption(captionLayout,0,0xf121f112,0,4,text.c_str());
    if(text!=lastCaption){lastCaption=text;log("LAYER2 CAPTION "+text);}
}
static std::vector<std::string> fields(const std::string& line) {
    std::vector<std::string> out;std::istringstream s(line);std::string x;
    while(std::getline(s,x,'\t')) out.push_back(x);
    return out;
}
static bool readTable(const std::wstring& name,std::map<std::wstring,std::wstring>& table) {
    std::ifstream input(name);if(!input)return false;std::string line;
    while(std::getline(input,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        if(line.empty()||line[0]=='#')continue;
        auto f=fields(line);if(f.size()!=2)return false;
        auto source=full((gameRoot+wide(f[0])).c_str());auto target=full((workRoot+wide(f[1])).c_str());
        if(source.compare(0,gameRoot.size(),gameRoot)||target.compare(0,lower(workRoot).size(),lower(workRoot)))return false;
        if(source.substr(gameRoot.size()).find(L"fdata_package\\data\\")!=0)return false;
        // Metadata only. Do not open or preload replacement payloads here.
        if(!table.emplace(source,target).second)return false;
    }
    return !table.empty();
}
static void loadCatalog() {
    std::ifstream names(gameRoot+L"REDELBE_LR\\slot_names.txt");std::string name;
    while(std::getline(names,name)) {
        if(!name.empty()&&name.back()=='\r')name.pop_back();
        if(name.empty()||name.size()>32||(name.find("_COS_")==std::string::npos&&name.find("_HAIR_")==std::string::npos&&name.find("_FACE_")==std::string::npos)||name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")!=std::string::npos)continue;
        uint32_t hash=0,power=31;for(unsigned char c:name){hash+=c*power;power*=31;}currentSlotNames[hash]=name;
    }
    std::ifstream input(workRoot+L"layer2.tsv");if(!input)return;
    // A manager profile may disable every Layer2 entry. Empty fallback/catalog
    // tables are valid together and leave all normal game resources untouched.
    bool hasVanilla=readTable(workRoot+L"vanilla.tsv",vanilla);
    std::string line;
    while(std::getline(input,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        if(line.empty()||line[0]=='#')continue;
        auto f=fields(line);if(f.size()!=3)throw std::runtime_error("Invalid Layer2 catalog");
        size_t used=0;unsigned long parsed=std::stoul(f[0],&used,16);
        if(used!=f[0].size())throw std::runtime_error("Invalid slot hash");
        Mod mod;mod.slot=static_cast<uint32_t>(parsed);mod.name=f[1];
        auto table=full((workRoot+wide(f[2])).c_str());
        if(table.compare(0,lower(workRoot).size(),lower(workRoot))||!readTable(table,mod.files))throw std::runtime_error("Invalid mod table");
        for(auto& entry:mod.files)if(!vanilla.count(entry.first))throw std::runtime_error("Missing vanilla resource");
        slots[mod.slot].push_back(mods.size());mods.push_back(std::move(mod));
    }
    if(!mods.empty()&&!hasVanilla)throw std::runtime_error("Invalid Layer2 vanilla table");
    enabled=true;
    log("LAYER2 catalog="+std::to_string(mods.size())+" mods; active=0; asset payloads not preloaded");
}
static std::wstring select(const std::wstring& path) {
    if(!enabled)return L"";
    std::lock_guard<std::recursive_mutex> guard(mutex);
    auto base=vanilla.find(path);if(base==vanilla.end())return L"";
    int player=routePlayer.load();if(player<0||player>1)player=0;
    // Battles can request resources for both players after the last preview request.
    // Search only the two active costumes, never every installed mod.
    for(int p:{player,1-player}) {
        // Explicit hair/head selections take precedence over a costume bundle.
        auto choices=hairChoices(activeHairs[p],activeFaces[p]);
        size_t h=hairSelections.current(p,activeHairs[p],activeFaces[p]);
        if(h&&h<=choices.size()) {
            auto& mod=mods[choices[h-1]];auto file=mod.files.find(path);
            if(file!=mod.files.end()){log("LAYER2 HAIR OPEN P"+std::to_string(p+1)+" "+mod.name+" "+utf8(path.substr(gameRoot.size())));return file->second;}
        }
        auto found=slots.find(activeCostumes[p]);
        size_t choice=selections.current(p,activeCostumes[p]);
        if(found!=slots.end()&&choice>0&&choice<=found->second.size()) {
            auto& mod=mods[found->second[choice-1]];auto file=mod.files.find(path);
            if(file!=mod.files.end()) {
                log("LAYER2 OPEN P"+std::to_string(p+1)+" "+mod.name+" "+utf8(path.substr(gameRoot.size())));
                return file->second;
            }
        }
    }
    log("LAYER2 BASE P"+std::to_string(player+1)+" "+utf8(path.substr(gameRoot.size())));
    return base->second;
}
static uintptr_t requestHook(void* object,uint32_t player,uint32_t chara,uint32_t costume,uint32_t face,uint32_t hair,uint32_t color,int hairColor) {
    if(player<2) {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        // A real costume/character change supersedes an outstanding manual reload.
        previewReloads[player].cancel();
        requests[player]={object,player,chara,costume,face,hair,color,hairColor};
        activeCostumes[player]=costume;activeHairs[player]=hair;activeFaces[player]=face;
        routePlayer=static_cast<int>(player);
        log("LAYER2 REQUEST P"+std::to_string(player+1)+" costume="+hex(costume)+" choice="+std::to_string(selections.current(player,costume)));
    }
    auto result=requestOriginal(object,player,chara,costume,face,hair,color,hairColor);
    if(player<2&&(selectedPlayer==static_cast<int>(player)||hairPlayer==static_cast<int>(player)))showSlotInfo();
    return result;
}
static void* randomHook(void* object,void* output,void* input,uint32_t player,bool userRandom,bool cpuRandom,uintptr_t unused,uint8_t character) {
    auto caller=reinterpret_cast<uintptr_t>(_ReturnAddress())-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    void* result=randomOriginal(object,output,input,player,userRandom,cpuRandom,unused,character);
    if(!enabled||player>=2||!output)return result;
    uint32_t costume;memcpy(&costume,static_cast<BYTE*>(output)+4,sizeof(costume));
    log("LAYER2 RANDOM EVENT P"+std::to_string(player+1)+" costume="+hex(costume)+" caller="+hex(static_cast<uint32_t>(caller))+" user="+std::to_string(userRandom));
    // Verified callers corresponding to the original Versus and Free Training hooks.
    // Arcade/Survival prefetch future opponents; do not activate their choices early.
    if(reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr))+caller!=gamecode::get("randomCaller1") && reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr))+caller!=gamecode::get("randomCaller2"))return result;
    uint64_t sample=0;
    if(BCryptGenRandom(nullptr,reinterpret_cast<PUCHAR>(&sample),sizeof(sample),BCRYPT_USE_SYSTEM_PREFERRED_RNG)<0) {
        log("LAYER2 RANDOM skipped: random source unavailable");return result;
    }
    std::lock_guard<std::recursive_mutex> guard(mutex);
    auto found=slots.find(costume);size_t total=found==slots.end()?0:found->second.size();
    size_t choice=static_cast<size_t>(sample%(total+1));
    Layer2RandomChoice pending;
    memcpy(&pending.character,output,1);
    pending.costume=costume;pending.choice=choice;
    memcpy(&pending.face,static_cast<BYTE*>(output)+8,4);
    memcpy(&pending.hair,static_cast<BYTE*>(output)+12,4);
    randomQueue.push(player,pending);
    std::string name=choice?mods[found->second[choice-1]].name:"Default";
    log("LAYER2 RANDOM QUEUED P"+std::to_string(player+1)+" "+name+" "+std::to_string(choice)+"/"+std::to_string(total));
    return result;
}
static void* loadHook(void* object,void* context,uint8_t character,void* slot,uint8_t extra) {
    if(enabled&&slot) {
        uint32_t values[3];memcpy(values,slot,sizeof(values));
        std::lock_guard<std::recursive_mutex> guard(mutex);
        unsigned player=0;Layer2RandomChoice pending;
        log("LAYER2 LOAD character="+std::to_string(character)+" costume="+hex(values[0])+" face="+hex(values[1])+" hair="+hex(values[2]));
        if(randomQueue.consume(character,values[0],values[1],values[2],player,pending)) {
            auto found=slots.find(pending.costume);size_t total=found==slots.end()?0:found->second.size();
            size_t choice=selections.random(player,pending.costume,total,pending.choice);
            activeCostumes[player]=pending.costume;activeHairs[player]=pending.hair;activeFaces[player]=pending.face;routePlayer=static_cast<int>(player);
            std::string name=choice?mods[found->second[choice-1]].name:"Default";
            log("LAYER2 RANDOM ACTIVATE P"+std::to_string(player+1)+" "+name+" costume="+hex(pending.costume));
        }
    }
    return loadOriginal(object,context,character,slot,extra);
}
static void finishPreviewReload(unsigned player,bool immediately=false) {
    Request req;
    {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        if(!previewReloads[player].take(GetTickCount64(),GetCurrentThreadId(),immediately))return;
        req=pendingRequests[player];
    }
    ReloadScope reload;
    requestHook(req.object,req.player,req.chara,req.costume,req.face,req.hair,req.color,req.hairColor);
    log("LAYER2 PREVIEW RELOAD P"+std::to_string(req.player+1)+" body_released=1 cache_misses="+
        std::to_string(reloadCacheMisses[0])+","+std::to_string(reloadCacheMisses[1])+","+
        std::to_string(reloadCacheMisses[2])+","+std::to_string(reloadCacheMisses[3]));
}
static void pumpPreviewReloads(){if(enabled){finishPreviewReload(0);finishPreviewReload(1);}}
static uintptr_t layoutHook(void* object,uint32_t hash,const char* animation,uint32_t extra) {
    captionLayout=object;
    // Finish before leaving the costume screen so no delayed request can restore
    // a stale preview after a menu transition. Natural requests cancel it too.
    if(animation&&!strcmp(animation,"cos_out_p1"))finishPreviewReload(0,true);
    if(animation&&!strcmp(animation,"cos_out_p2"))finishPreviewReload(1,true);
    if(animation&&!strcmp(animation,"detail_out")&&hairPlayer>=0)finishPreviewReload(static_cast<unsigned>(hairPlayer.load()),true);
    auto result=layoutOriginal(object,hash,animation,extra);
    if(!animation)return result;
    if(layoutLogs++<400||!strncmp(animation,"detail_",7)||!strncmp(animation,"cos_",4))log("LAYER2 ANIMATION "+hex(hash)+" "+animation);
    if(hash==0xdd6728d2) {
        if(!strcmp(animation,"detail_pos_1p")){hairPlayer=0;showSlotInfo();}
        else if(!strcmp(animation,"detail_pos_2p")){hairPlayer=1;showSlotInfo();}
        else if(!strcmp(animation,"detail_out")){hairPlayer=-1;showSlotInfo();}
    }
    // These names belong to the game's costume selection UI, not arbitrary input states.
    if(!strcmp(animation,"cos_in_p1")){std::lock_guard<std::recursive_mutex> guard(mutex);randomQueue.clear();selectedPlayer=0;}
    else if(!strcmp(animation,"cos_in_p2")){std::lock_guard<std::recursive_mutex> guard(mutex);randomQueue.clear();selectedPlayer=1;}
    else if(!strcmp(animation,"cos_out_p1")&&selectedPlayer==0)selectedPlayer=-1;
    else if(!strcmp(animation,"cos_out_p2")&&selectedPlayer==1)selectedPlayer=-1;
    if(!strcmp(animation,"cos_in_p1")||!strcmp(animation,"cos_in_p2")||
       (hash==0xf121f112&&!strcmp(animation,"caption_in")))showSlotInfo();
    return result;
}
static bool cacheCheck(unsigned index,void*a,uintptr_t b,uintptr_t c,uintptr_t d) {
    if(forceReload && (!preservedBody || static_cast<uint32_t>(b)!=preservedBody)){++reloadCacheMisses[index];return false;}
    return cacheOriginal[index](a,b,c,d);
}
static bool cache0(void*a,uintptr_t b,uintptr_t c,uintptr_t d){
    // The scale consumer has its own costume-ID check before calling the
    // initializer. Same-slot replacement must reach that initializer so its
    // model identity check can rebuild the vectors. The consumer's +169 flag
    // already limits this path to once per newly loaded model.
    if(_ReturnAddress()==modelScaleCacheReturn)return false;
    if(rebuildModelDefaults && _ReturnAddress()==modelDefaultsCacheReturn)return false;
    return cacheCheck(0,a,b,c,d);
}
static void modelDefaultsHook(void* unused,void* owner,uint8_t part) {
    bool changed=false;
    if(owner && part<3) {
        // Native 22cbe80 maps parts 0/1/2 to shared requests at +70/+38/+0.
        // 22ca6e0 requires both +60 and +68 to be ready before rebuilding.
        auto request=*reinterpret_cast<BYTE**>(static_cast<BYTE*>(owner)+(2-part)*0x38);
        Layer2ModelSource source;
        if(request)source={reinterpret_cast<uintptr_t>(request),
            *reinterpret_cast<uintptr_t*>(request+0x60),*reinterpret_cast<uintptr_t*>(request+0x68)};
        std::lock_guard<std::recursive_mutex> guard(mutex);
        changed=modelSources.changed(reinterpret_cast<uintptr_t>(owner),part,source);
    }
    struct Scope {
        bool previous=rebuildModelDefaults;
        Scope(bool value){rebuildModelDefaults=value;}
        ~Scope(){rebuildModelDefaults=previous;}
    } scope(changed);
    modelDefaultsOriginal(unused,owner,part);
    if(changed)log("LAYER2 MODEL DEFAULTS rebuilt part="+std::to_string(part));
}
static bool cache1(void*a,uintptr_t b,uintptr_t c,uintptr_t d){return cacheCheck(1,a,b,c,d);}
// The inner body/face and hair checks control reuse of the actual async requests.
// Bypassing only the two outer checks leaves those requests cached in LR.
static bool cache2(void*a,uintptr_t b,uintptr_t c,uintptr_t d){return cacheCheck(2,a,b,c,d);}
static bool cache3(void*a,uintptr_t b,uintptr_t c,uintptr_t d){return cacheCheck(3,a,b,c,d);}
static void cycle(int direction,const char* input) {
    if(!enabled)return;
    Request req;size_t value=0,total=0;std::string name;
    {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        bool hairMode=hairPlayer.load()>=0;
        int p=hairMode?hairPlayer.load():selectedPlayer.load();if(p<0||p>1){log(std::string("LAYER2 INPUT ignored outside costume screen: ")+input);return;}
        req=requests[p];auto found=slots.find(req.costume);
        auto choices=hairMode?hairChoices(req.hair,req.face):(found!=slots.end()?found->second:std::vector<size_t>{});
        if(!req.object||choices.empty())return;
        if(previewReloads[p].pending)return;
        static ULONGLONG next=0;auto now=GetTickCount64();if(now<next)return;next=now+350;
        total=choices.size();value=hairMode?hairSelections.cycle(p,req.hair,total,direction,req.face):selections.cycle(p,req.costume,total,direction);
        name=value?mods[choices[value-1]].name:"Default";
        routePlayer=p;
    }
    log("LAYER2 SELECT P"+std::to_string(req.player+1)+" "+name+" "+std::to_string(value)+"/"+std::to_string(total)+" input="+input);
    showSlotInfo();
    if(hairPlayer>=0) {
        // Retain the loaded body and let LR replace face/hair requests through
        // its normal asynchronous transition. No release timer or empty-body gap.
        ReloadScope reload;
        struct PreserveBody {uint32_t previous=preservedBody;PreserveBody(uint32_t slot){preservedBody=slot;}~PreserveBody(){preservedBody=previous;}} preserve(req.costume);
        requestHook(req.object,req.player,req.chara,req.costume,req.face,req.hair,req.color,req.hairColor);
        log("LAYER2 HAIR NATIVE TRANSITION P"+std::to_string(req.player+1)+" body_retained=1 delayed_release=0");
        return;
    }
    // Native body request handle, verified in request_character_with_id:
    // model object + 0x98 + player*0x2d8. Face/hair handles follow at +0x38/+0x70.
    // The native clear function cancels the body request, drops its shared
    // ownership and clears the pending callback; never free game memory here.
    auto handle=static_cast<BYTE*>(req.object)+0x98+req.player*0x2d8;
    releaseBody(req.object,handle);
    {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        pendingRequests[req.player]=req;
        previewReloads[req.player].begin(GetTickCount64(),GetCurrentThreadId());
    }
    log("LAYER2 BODY RELEASE P"+std::to_string(req.player+1)+" costume="+hex(req.costume));
}
static DWORD WINAPI xinputHook(DWORD player,XINPUT_STATE* state) {
    DWORD ret=xinputOriginal(player,state);
    pumpPreviewReloads();
    static DWORD previous[4]{};
    if(ret==ERROR_SUCCESS&&player<4) {
        DWORD buttons=state->Gamepad.wButtons|(state->Gamepad.bLeftTrigger>128?0x10000:0);
        DWORD edge=buttons&~previous[player];previous[player]=buttons;
        if(edge&XINPUT_GAMEPAD_BACK)cycle(-1,"Select/Back");
        else if(edge&0x10000)cycle(1,"L2/LT");
    }
    return ret;
}
static HRESULT WINAPI keyboardHook(void* device,DWORD length,void* buffer) {
    using Fn=HRESULT(WINAPI*)(void*,DWORD,void*);
    auto original=reinterpret_cast<Fn>((*reinterpret_cast<void***>(device))[9]);
    HRESULT result=original(device,length,buffer);
    pumpPreviewReloads();
    static bool previous=false;
    if(SUCCEEDED(result)&&length==256) {
        bool down=(static_cast<unsigned char*>(buffer)[0x21]&0x80)!=0;
        bool edge=down&&!previous;previous=down;if(edge)cycle(1,"F");
    }
    return result;
}
struct Hook { BYTE* target;std::vector<BYTE> expected;void* replacement;void** original;BYTE* trampoline=nullptr; };
static std::vector<BYTE> bytes(const char* s) {
    std::vector<BYTE> out;std::istringstream in(s);unsigned n;while(in>>std::hex>>n)out.push_back(static_cast<BYTE>(n));return out;
}
static void absoluteJump(BYTE* memory,void* destination) {
    const BYTE op[6]={0xff,0x25,0,0,0,0};memcpy(memory,op,6);memcpy(memory+6,&destination,8);
}
static void write(BYTE* target,const BYTE* data,size_t size) {
    DWORD old;if(!VirtualProtect(target,size,PAGE_EXECUTE_READWRITE,&old))throw std::runtime_error("Hook protection failed");
    memcpy(target,data,size);FlushInstructionCache(GetCurrentProcess(),target,size);DWORD ignored;VirtualProtect(target,size,old,&ignored);
}
static BYTE* allocateNear(BYTE* address) {
    SYSTEM_INFO si;GetSystemInfo(&si);uintptr_t gran=si.dwAllocationGranularity;uintptr_t center=reinterpret_cast<uintptr_t>(address)&~(gran-1);
    for(uintptr_t delta=gran;delta<0x70000000;delta+=gran) {
        for(int direction:{-1,1}) {
            uintptr_t wanted=direction<0?center-delta:center+delta;
            if(auto result=VirtualAlloc(reinterpret_cast<void*>(wanted),0x1000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE))return static_cast<BYTE*>(result);
        }
    }
    throw std::runtime_error("No nearby relay memory");
}
// The native UTF-16 pane setter copies its input synchronously.
using TitleTextFn=void(*)(void*,uintptr_t,uint32_t,uint32_t,uint32_t,const wchar_t*,uint32_t);
static TitleTextFn titleTextOriginal;
static bool isVersionText(const wchar_t* text,uint32_t length) {
    if(!text||length<4||length>24)return false;
    uint32_t n=length;while(n&&(text[n-1]==0||text[n-1]==L' '))--n;
    if(n<4)return false;
    uint32_t i=0;
    if(n>4&&!_wcsnicmp(text,L"Ver.",4))i=4;
    else if(text[0]==L'v'||text[0]==L'V')i=1;
    else return false;
    while(i<n&&text[i]==L' ')++i;
    bool dot=false,digit=false;
    for(;i<n;++i){if(text[i]>=L'0'&&text[i]<=L'9'){digit=true;continue;}if(text[i]==L'.'&&digit){dot=true;digit=false;continue;}return false;}
    return dot&&digit;
}
static std::wstring brandingLabel() {
    std::wstring path=gameRoot+L"REDELBE_LR\\branding.ini";
    if(GetFileAttributesW(path.c_str())==INVALID_FILE_ATTRIBUTES) {
        HANDLE f=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(f!=INVALID_HANDLE_VALUE){const char* data="; UTF-8. Edit Name and Version, then return to the title screen or restart.\r\n[Branding]\r\nEnabled=1\r\nName=Raikiri\r\nVersion=0.3 RC4\r\n";DWORD count;WriteFile(f,data,(DWORD)strlen(data),&count,nullptr);CloseHandle(f);}
    }
    std::ifstream in(path);std::string line,name="Raikiri",version="0.3 RC4";bool on=true,section=false;
    while(std::getline(in,line)) {
        if(line.size()>=3&&line.compare(0,3,"\xef\xbb\xbf")==0)line.erase(0,3);
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        if(!line.empty()&&line.front()=='['){section=line=="[Branding]";continue;}
        if(!section)continue;
        if(line.rfind("Name=",0)==0)name=line.substr(5,64);
        if(line.rfind("Version=",0)==0)version=line.substr(8,24);
        if(line=="Enabled=0")on=false;
    }
    if(!on)return L"";
    auto label=wide(name+(version.empty()?"":" "+version));
    label.erase(std::remove_if(label.begin(),label.end(),[](wchar_t c){return c<32;}),label.end());
    return label;
}
static void titleTextHook(void* object,uintptr_t unused,uint32_t pane,uint32_t index,uint32_t type,const wchar_t* text,uint32_t length) {
    if(pane==0xb281b468&&isVersionText(text,length)) {
        auto label=brandingLabel();
        if(!label.empty()) {
            size_t n=length;while(n&&(text[n-1]==0||text[n-1]==L' '))--n;
            std::wstring combined(text,n);combined+=L"  ";combined+=label;
            log("TITLE BRANDING pane="+hex(pane)+" text="+utf8(combined));
            titleTextOriginal(object,unused,pane,index,type,combined.c_str(),static_cast<uint32_t>(combined.size()));return;
        }
    }
    titleTextOriginal(object,unused,pane,index,type,text,length);
}
static void install() {
    if(!enabled)return;
    BYTE* base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
    gamecode::resolve(base);
    gamecode::xinputCell(base);
    for(const auto& entry:gamecode::resolved)log("PATTERN "+entry.first+" rva="+hex(static_cast<uint32_t>(entry.second-base)));
    auto captionBytes=bytes("40 53 55 56 57 41 56 48 81 ec 10 01 00 00");
    if(memcmp(gamecode::get("caption"),captionBytes.data(),captionBytes.size()))throw std::runtime_error("Caption setter signature mismatch");
    setCaption=reinterpret_cast<CaptionFn>(gamecode::get("caption"));
    auto releaseBytes=bytes("40 57 48 83 ec 50 48 c7 44 24 28 fe ff ff ff");
    if(memcmp(gamecode::get("release"),releaseBytes.data(),releaseBytes.size()))throw std::runtime_error("Body release signature mismatch");
    releaseBody=reinterpret_cast<ReleaseFn>(gamecode::get("release"));
    auto defaultsCall=bytes("84 c0");
    if(memcmp(gamecode::get("defaults")+0xf1,defaultsCall.data(),defaultsCall.size()))throw std::runtime_error("Model defaults cache callsite mismatch");
    modelDefaultsCacheReturn=gamecode::get("defaults")+0xf1;
    auto scaleCall=bytes("84 c0");
    if(memcmp(gamecode::get("scale")+0x137,scaleCall.data(),scaleCall.size()))throw std::runtime_error("Model scale cache callsite mismatch");
    modelScaleCacheReturn=gamecode::get("scale")+0x137;
    // Exact, whole-instruction prologues, each with no relative instruction.
    // No generic instruction relocation is attempted. Unsupported builds fail closed.
    std::vector<Hook> hooks={
        {gamecode::get("titleText"),bytes("48 89 5c 24 08 48 89 74 24 10 57 48 83 ec 20"),(void*)titleTextHook,(void**)&titleTextOriginal},
        {gamecode::get("defaults"),bytes("40 55 56 57 41 54 41 55 41 56 41 57 48 81 ec d0 01 00 00"),(void*)modelDefaultsHook,(void**)&modelDefaultsOriginal},
        {gamecode::get("request"),bytes("40 55 56 57 41 54 41 55 41 56 41 57 48 8d 6c 24 d0"),(void*)requestHook,(void**)&requestOriginal},
        {gamecode::get("layout"),bytes("40 55 56 57 41 54 41 55 41 56 41 57 48 8d 6c 24 d9"),(void*)layoutHook,(void**)&layoutOriginal},
        {gamecode::get("random"),bytes("48 8b c4 44 88 48 20 48 89 50 10 56 57 41 56"),(void*)randomHook,(void**)&randomOriginal},
        {gamecode::get("load"),bytes("48 89 4c 24 08 55 56 57 41 56 41 57 48 83 ec 30"),(void*)loadHook,(void**)&loadOriginal},
        {gamecode::get("cache0"),bytes("4c 89 44 24 18 4c 89 4c 24 20 53 57 48 83 ec 28"),(void*)cache0,(void**)&cacheOriginal[0]},
        {gamecode::get("cache1"),bytes("48 89 5c 24 10 48 89 74 24 18 57 48 83 ec 20"),(void*)cache1,(void**)&cacheOriginal[1]},
        {gamecode::get("cache2"),bytes("40 53 56 57 48 83 ec 30 48 8b d9 41 8b f8"),(void*)cache2,(void**)&cacheOriginal[2]},
        {gamecode::get("cache3"),bytes("40 53 55 56 57 48 83 ec 28 48 8b d9 41 8b f9"),(void*)cache3,(void**)&cacheOriginal[3]}
    };
    BYTE* keyboard=gamecode::get("keyboard");
    auto keyboardBytes=bytes("48 8b 01 ff 50 48");
    if(memcmp(keyboard,keyboardBytes.data(),6))throw std::runtime_error("Keyboard callsite mismatch");
    for(auto& hook:hooks)if(memcmp(hook.target,hook.expected.data(),hook.expected.size()))throw std::runtime_error("Layer2 prologue mismatch");
    for(auto& hook:hooks) {
        hook.trampoline=static_cast<BYTE*>(VirtualAlloc(nullptr,0x1000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
        if(!hook.trampoline)throw std::runtime_error("Trampoline allocation failed");
        memcpy(hook.trampoline,hook.expected.data(),hook.expected.size());absoluteJump(hook.trampoline+hook.expected.size(),hook.target+hook.expected.size());
        DWORD old;VirtualProtect(hook.trampoline,0x1000,PAGE_EXECUTE_READ,&old);*hook.original=hook.trampoline;
    }
    BYTE* relay=allocateNear(keyboard);absoluteJump(relay,(void*)keyboardHook);DWORD old;VirtualProtect(relay,0x1000,PAGE_EXECUTE_READ,&old);
    // ASI startup runs before selection code. Install only after every signature passes.
    for(auto& hook:hooks){std::vector<BYTE> patch(hook.expected.size(),0x90);absoluteJump(patch.data(),hook.replacement);write(hook.target,patch.data(),patch.size());}
    BYTE call[6]={0x90,0xe8,0,0,0,0};int32_t displacement=static_cast<int32_t>(relay-(keyboard+6));memcpy(call+2,&displacement,4);write(keyboard,call,6);
    auto cell=gamecode::xinputCell(base);
    xinputOriginal=reinterpret_cast<decltype(xinputOriginal)>(*cell);
    void* replacement=(void*)xinputHook;write(reinterpret_cast<BYTE*>(cell),reinterpret_cast<BYTE*>(&replacement),sizeof(replacement));
    log("LAYER2 installed model/layout/four-cache/model-defaults/keyboard/XInput hooks; Default selected for every player/slot");
}
}

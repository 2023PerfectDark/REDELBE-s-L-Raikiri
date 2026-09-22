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
#include "layer2_roster.h"
#include "roster_fade.h"
#include "battle_hud.h"
#include "game_patterns.h"
#include "stage_pattern.h"
#include "stage_slot.h"
#include "hair_slot_pattern.h"
#include "layer2_private_route.h"
#include "private_companion_pattern.h"
#include "private_battle_pattern.h"
#include "animation_trace_patterns.h"
#include "animation_preview_test.h"
#include "animation_trace.h"

namespace l2 {
struct Mod { std::string name; std::wstring iniPath; uint32_t slot; std::map<std::wstring,std::wstring> files; Layer2PrivateRoute privateRoute; };
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
using BattleOwnerFn=void*(*)(void*,void*,uint8_t,uint8_t,void*,uint8_t);
static BattleOwnerFn battleOwnerOriginal;
static thread_local int battleOwnerPlayer=-1;
static void* battleOwnerHook(void* result,void* context,uint8_t player,uint8_t character,void* slot,uint8_t extra) {
    struct Scope {int previous=battleOwnerPlayer;Scope(int p){battleOwnerPlayer=p;}~Scope(){battleOwnerPlayer=previous;}} scope(player<2?player:-1);
    return battleOwnerOriginal(result,context,player,character,slot,extra);
}
static Layer2RandomQueue randomQueue;
using RequestFn=uintptr_t(*)(void*,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,int);
using LayoutFn=uintptr_t(*)(void*,uint32_t,const char*,uint32_t);
using CacheFn=bool(*)(void*,uintptr_t,uintptr_t,uintptr_t);
static RequestFn requestOriginal;
using CompanionFn=uint32_t(*)(uint32_t,uint32_t);
static std::string hex(uint32_t n);
static CompanionFn companionOriginal;
// Built once before hooks are installed; safe for concurrent native readers.
static std::map<uint32_t,uint32_t> privateCompanionSources;
static std::set<uint32_t> privateHairModels;
using PrivateHairFn=uint32_t(*)(uint32_t);
static PrivateHairFn privateHairOriginal;
static uint32_t privateHairHook(uint32_t hair) {
    // These IDs already have independently registered model chains. The normal
    // wardrobe table has no row for them and would otherwise turn them into 0.
    if(privateHairModels.count(hair))return hair;
    return privateHairOriginal(hair);
}
static std::atomic<unsigned> privateCompanionLogs{0};
static uint32_t companionHook(uint32_t category,uint32_t model) {
    auto value=companionOriginal(category,model);
    if(value)return value;
    auto it=privateCompanionSources.find(model);
    if(it==privateCompanionSources.end())return value;
    value=companionOriginal(category,it->second);
    if(privateCompanionLogs.fetch_add(1)<30)
        log("LAYER2 PRIVATE COMPANION category="+hex(category)+" work="+hex(model)+" source="+hex(it->second)+" result="+hex(value));
    return value;
}
static LayoutFn layoutOriginal;
using LayoutVisibilityFn=void(*)(void*,uint32_t);
static LayoutVisibilityFn layoutShowOriginal,layoutHideOriginal;
static Layer2Roster roster;
static BattleHudState battleHud;
static std::vector<uint32_t> rosterInstances;
static void* rosterInstanceOwner=nullptr;
static std::atomic<ULONGLONG> rosterBackAt{0};
using LayoutObjectFn=void*(*)(void*,uintptr_t,uint32_t,uintptr_t);
static LayoutObjectFn layoutObject;
using RosterColorFn=uint32_t(*)(void*,uint32_t);
static RosterColorFn rosterColorOriginal;
static std::vector<void*> fadingRosterLayouts;
static RosterFadeHover rosterHover;
static std::atomic<ULONGLONG> rosterFadeAt{0};
static std::atomic<unsigned> rosterFadeReads{0};
using AnimationResetFn=void(*)(void*,uint32_t,const char*,uint32_t);
using AnimationPlayingFn=bool(*)(void*,uint32_t,const char*,uint32_t);
static AnimationResetFn animationReset;
static AnimationPlayingFn animationPlaying;
static void* rosterExitOwner=nullptr;
static DWORD rosterExitThread=0;
static bool rosterExitPose=false;
static void* rosterBaseOwner=nullptr;
static uint32_t rosterBaseInstance=0;
static constexpr uint32_t rosterBase=0xbbf9987c;
static void finishRosterExit() {
    if(!rosterExitOwner||GetCurrentThreadId()!=rosterExitThread)return;
    if(rosterBaseOwner==rosterExitOwner&&animationPlaying(rosterExitOwner,rosterBase,"icon_pos_out",rosterBaseInstance))return;
    for(auto instance:rosterInstances)if(animationPlaying(rosterExitOwner,Layer2Roster::portraits,"icon_out",instance))return;
    if(roster.hidden)layoutHideOriginal(rosterExitOwner,Layer2Roster::portraits);
    rosterExitOwner=nullptr;
    log("UI ROSTER native exit complete");
}
static uint32_t rosterColorHook(void* pane,uint32_t vertex) {
    auto color=rosterColorOriginal(pane,vertex);
    auto start=rosterFadeAt.load();if(!start)return color;
    auto duration=userconfig::current.number("UI","roster_fade_ms");
    auto elapsed=GetTickCount64()-start;if(elapsed>=duration)return color;
    std::lock_guard<std::recursive_mutex> guard(mutex);
    auto owner=*reinterpret_cast<void**>(static_cast<BYTE*>(pane)+0xd8);
    if(std::find(fadingRosterLayouts.begin(),fadingRosterLayouts.end(),owner)==fadingRosterLayouts.end())return color;
    if(start!=rosterFadeAt.load())return color;
    float t=userconfig::current.flag("UI","roster_hover_reveal")?
        rosterHover.alpha(reinterpret_cast<uintptr_t>(owner),elapsed,duration):RosterFadeHover::ramp(elapsed,duration);
    ++rosterFadeReads;
    return (color&0x00ffffff)|(static_cast<uint32_t>((color>>24)*t)<<24);
}
static void layoutShowHook(void* object,uint32_t hash) {
    std::lock_guard<std::recursive_mutex> guard(mutex);
    if(userconfig::current.flag("UI","enable_hide_battle_hud")) {
        battleHud.bind(reinterpret_cast<uintptr_t>(object));
        if(!battleHud.show(hash))return;
    }
    if(hash==Layer2Roster::portraits&&roster.hidden)return;
    layoutShowOriginal(object,hash);
}
static void layoutHideHook(void* object,uint32_t hash) {
    std::lock_guard<std::recursive_mutex> guard(mutex);
    if(userconfig::current.flag("UI","enable_hide_battle_hud")) {
        battleHud.bind(reinterpret_cast<uintptr_t>(object));battleHud.hide(hash);
    }
    layoutHideOriginal(object,hash);
}
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
static CaptionFn stageTextureOriginal;
static bool stageScreen=false;
static DWORD stageVideoUiThread=0;
static std::string stageCaption;
static void showStageInfo() {
    if(stageScreen&&setCaption&&captionLayout&&!stageCaption.empty()&&userconfig::current.flag("Misc","slot_info_in_sss"))
        setCaption(captionLayout,0,0xf121f112,0,4,stageCaption.c_str());
}
static void stageTextureHook(void* object,uintptr_t unused,uint32_t layout,uint32_t index,uint32_t pane,const char* texture) {
    stageTextureOriginal(object,unused,layout,index,pane,texture);
    if(layout!=0xd0805c2d||!texture)return;
    stageVideoUiThread=GetCurrentThreadId();
    std::lock_guard<std::recursive_mutex> guard(mutex);
    auto caption=stageinfo::caption(texture);
    if(caption.empty())return;
    captionLayout=object;stageScreen=true;
    if(caption!=stageCaption)log("STAGE CAPTION texture="+std::string(texture)+" pane="+std::to_string(pane)+" "+caption);
    stageCaption=caption;showStageInfo();
}
static std::string lastCaption;
static std::map<uint32_t,std::string> currentSlotNames;
static std::string hex(uint32_t n) { char b[16];sprintf_s(b,"%08x",n);return b; }
#include "hair_color_menu.h"
static void showSlotInfo() {
    if(stageScreen){showStageInfo();return;}
    if(!enabled||!setCaption||!captionLayout||!userconfig::current.flag("Misc","slot_info_in_css"))return;
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
    haircolor::initialize();
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
        mod.iniPath=table.substr(0,table.find_last_of(L"/\\")+1)+L"mod.ini";
        // Experimental prepared profiles only; absent section preserves existing behavior.
        mod.privateRoute.enabled=GetPrivateProfileIntW(L"PrivateModel",L"enabled",0,mod.iniPath.c_str())!=0;
        if(mod.privateRoute.enabled) {
            const wchar_t* sourceKeys[]{L"source_costume",L"source_face",L"source_hair"};
            const wchar_t* workKeys[]{L"work_costume",L"work_face",L"work_hair"};
            for(unsigned i=0;i<3;++i) {
                mod.privateRoute.source[i]=GetPrivateProfileIntW(L"PrivateModel",sourceKeys[i],0,mod.iniPath.c_str());
                mod.privateRoute.work[i]=GetPrivateProfileIntW(L"PrivateModel",workKeys[i],0,mod.iniPath.c_str());
            }
            mod.privateRoute.donorCharacter=GetPrivateProfileIntW(L"PrivateModel",L"donor_character",0,mod.iniPath.c_str());
            unsigned count=GetPrivateProfileIntW(L"PrivateModel",L"count",0,mod.iniPath.c_str());
            if(count>4096)throw std::runtime_error("Too many private model aliases");
            for(unsigned i=0;i<count;++i){
                auto suffix=std::to_wstring(i);
                auto source=GetPrivateProfileIntW(L"PrivateModel",(L"source_"+suffix).c_str(),0,mod.iniPath.c_str());
                auto work=GetPrivateProfileIntW(L"PrivateModel",(L"work_"+suffix).c_str(),0,mod.iniPath.c_str());
                if(!source||!work||source==work||!mod.privateRoute.aliases.emplace(source,work).second)throw std::runtime_error("Invalid private model alias");
            }
        }
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
    if(path.find(L"0x0fa9")!=std::wstring::npos)log("LAYER2 PRIVATE ASSET "+utf8(path.substr(gameRoot.size())));
    int player=routePlayer.load();if(player<0||player>1)player=0;
    // Battles can request resources for both players after the last preview request.
    // Search only the two active costumes, never every installed mod.
    for(int p:{player,1-player}) {
        // Explicit hair/head selections take precedence over a costume bundle.
        auto choices=hairChoices(activeHairs[p],activeFaces[p]);
        size_t h=hairSelections.current(p,activeHairs[p],activeFaces[p]);
        if(h&&h<=choices.size()) {
            auto& mod=mods[choices[h-1]];auto file=mod.files.find(path);
            if(file!=mod.files.end()){if(userconfig::current.flag("Debug","log_virtual"))log("LAYER2 HAIR OPEN P"+std::to_string(p+1)+" "+mod.name+" "+utf8(path.substr(gameRoot.size())));return file->second;}
        }
        auto found=slots.find(activeCostumes[p]);
        size_t choice=selections.current(p,activeCostumes[p]);
        if(found!=slots.end()&&choice>0&&choice<=found->second.size()) {
            auto& mod=mods[found->second[choice-1]];auto file=mod.files.find(path);
            if(file!=mod.files.end()) {
                if(userconfig::current.flag("Debug","log_virtual"))log("LAYER2 OPEN P"+std::to_string(p+1)+" "+mod.name+" "+utf8(path.substr(gameRoot.size())));
                return file->second;
            }
        }
    }
    // Loose RRPreview resources are global; explicit character Layer2 wins above.
    auto global=slots.find(0xda5c95d8); // hash of reserved RRPREVIEW catalog group
    if(global!=slots.end())for(auto index:global->second) {
        auto file=mods[index].files.find(path);
        if(file!=mods[index].files.end()) {
            log("RRPREVIEW OPEN "+utf8(path.substr(gameRoot.size())));
            return file->second;
        }
    }
    if(userconfig::current.flag("Debug","log_virtual"))log("LAYER2 BASE P"+std::to_string(player+1)+" "+utf8(path.substr(gameRoot.size())));
    return base->second;
}
static bool applyPrivateSelection(unsigned player,const uint32_t (&original)[3],uint32_t (&parts)[3]) {
    bool changed=false;
    auto apply=[&](const Layer2PrivateRoute& route) {
        uint32_t candidate[]{original[0],original[1],original[2]};
        if(!route.apply(requests[1-player].chara,candidate))return;
        for(unsigned i=0;i<3;++i)if(candidate[i]!=original[i]){parts[i]=candidate[i];changed=true;}
    };
    auto found=slots.find(original[0]);size_t choice=selections.current(player,original[0]);
    if(found!=slots.end()&&choice&&choice<=found->second.size())apply(mods[found->second[choice-1]].privateRoute);
    auto choices=hairChoices(original[2],original[1]);
    size_t hairChoice=hairSelections.current(player,original[2],original[1]);
    if(hairChoice&&hairChoice<=choices.size())apply(mods[choices[hairChoice-1]].privateRoute);
    return changed;
}
static uintptr_t requestHook(void* object,uint32_t player,uint32_t chara,uint32_t costume,uint32_t face,uint32_t hair,uint32_t color,int hairColor) {
    if(player<2) {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        // A real costume/character change supersedes an outstanding manual reload.
        previewReloads[player].cancel();
        requests[player]={object,player,chara,costume,face,hair,color,hairColor};
        activeCostumes[player]=costume;activeHairs[player]=hair;activeFaces[player]=face;
        routePlayer=static_cast<int>(player);
        haircolor::bindPlayer(player,chara,hair);
        log("LAYER2 REQUEST P"+std::to_string(player+1)+" costume="+hex(costume)+" choice="+std::to_string(selections.current(player,costume)));
    }
    uint32_t modelParts[]{costume,face,hair};
    if(player<2) {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        const uint32_t original[]{costume,face,hair};
        if(applyPrivateSelection(player,original,modelParts))
            log("LAYER2 PRIVATE REQUEST P"+std::to_string(player+1)+" costume="+hex(modelParts[0])+" face="+hex(modelParts[1])+" hair="+hex(modelParts[2]));
    }
    auto result=requestOriginal(object,player,chara,modelParts[0],modelParts[1],modelParts[2],color,hairColor);
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
    size_t choice=userconfig::current.flag("Random","enable_random_costume_mods")?static_cast<size_t>(sample%(total+1)):0;
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
    // Native outer constructor supplies the fighter index. Never infer it from
    // costume hashes or request order: both fighters can use the same costume.
    alignas(16) unsigned char privateSlot[28]{};
    bool routed=false;
    if(enabled&&slot) {
        uint32_t values[3];memcpy(values,slot,sizeof(values));
        std::lock_guard<std::recursive_mutex> guard(mutex);
        unsigned player=0;Layer2RandomChoice pending;
        log("LAYER2 LOAD character="+std::to_string(character)+" costume="+hex(values[0])+" face="+hex(values[1])+" hair="+hex(values[2]));
        if(!privateCompanionSources.empty()) {
            std::ostringstream trace;
            trace<<"LAYER2 PRIVATE BATTLE TRACE player="<<battleOwnerPlayer<<" object="<<object<<" context="<<context<<" extra="<<unsigned(extra)
                 <<" caller="<<std::hex<<(reinterpret_cast<uintptr_t>(_ReturnAddress())-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)));
            unsigned char bytes[32]{};SIZE_T got=0;
            if(ReadProcessMemory(GetCurrentProcess(),context,bytes,sizeof(bytes),&got)&&got==sizeof(bytes)) {
                trace<<" context_words=";for(unsigned i=0;i<8;++i){uint32_t word;memcpy(&word,bytes+4*i,4);trace<<word<<",";}
            }
            log(trace.str());
        }
        haircolor::beginBattleHair(values[2]);
        if(randomQueue.consume(character,values[0],values[1],values[2],player,pending)) {
            auto found=slots.find(pending.costume);size_t total=found==slots.end()?0:found->second.size();
            size_t choice=selections.random(player,pending.costume,total,pending.choice);
            activeCostumes[player]=pending.costume;activeHairs[player]=pending.hair;activeFaces[player]=pending.face;routePlayer=static_cast<int>(player);
            std::string name=choice?mods[found->second[choice-1]].name:"Default";
            log("LAYER2 RANDOM ACTIVATE P"+std::to_string(player+1)+" "+name+" costume="+hex(pending.costume));
        }
        if(battleOwnerPlayer>=0 && battleOwnerPlayer<2) {
            unsigned owner=static_cast<unsigned>(battleOwnerPlayer);
            const uint32_t original[]{values[0],values[1],values[2]};
            routed=applyPrivateSelection(owner,original,values);
            if(routed) {
                memcpy(privateSlot,slot,sizeof(privateSlot));memcpy(privateSlot,values,sizeof(values));
                log("LAYER2 PRIVATE BATTLE P"+std::to_string(owner+1)+" costume="+hex(values[0])+" face="+hex(values[1])+" hair="+hex(values[2]));
            }
        }
    }
    return loadOriginal(object,context,character,routed?privateSlot:slot,extra);
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
static void pumpPreviewReloads(){if(enabled){finishPreviewReload(0);finishPreviewReload(1);}
    finishRosterExit();
    auto start=rosterFadeAt.load();
    if(start&&GetTickCount64()-start>=userconfig::current.number("UI","roster_fade_ms")&&rosterFadeAt.compare_exchange_strong(start,0))log("UI ROSTER fade color reads="+std::to_string(rosterFadeReads.load()));
}
#include "mouse_menu.h"
static void pumpHairColor(){
    updatenotice::animateColor();
    birthdays::display::sync();
    noticedisplay::sync();
    wardrobevoice::sync(haircolor::visible.load()&&haircolor::expanded.load()&&mousemenu::wardrobePreview());
    tickets::display::sync(mousemenu::wardrobePreview());
    bool wardrobe=mousemenu::screen==5||mousemenu::screen==6||(mousemenu::screen==0&&(mousemenu::rowHash==0x8f2023d0||mousemenu::rowHash==0x7454be7b||mousemenu::rowHash==0x534d6e7c));
    bool menu=mousemenu::active&&!mousemenu::dialog&&mousemenu::screen==0&&mousemenu::rowHash==0x8f2023d0;
    if(!wardrobe&&!haircolor::context)return;
    unsigned slot=mousemenu::customSlotIndex;
    std::lock_guard<std::recursive_mutex> guard(mutex);
    auto req=requests[0];haircolor::sync(wardrobe&&slot<10&&req.object,menu,req.hair,req.chara,slot);
    if(haircolor::take()){
        ReloadScope reload;
        struct PreserveBody{uint32_t old=preservedBody;PreserveBody(uint32_t n){preservedBody=n;}~PreserveBody(){preservedBody=old;}} preserve(req.costume);
        requestHook(req.object,req.player,req.chara,req.costume,req.face,req.hair,req.color,req.hairColor);
        log("HAIR COLOR prototype selected="+std::to_string(haircolor::current.load())+" hair="+hex(req.hair)+" custom_slot="+std::to_string(slot));
    }
}
static uintptr_t layoutHook(void* object,uint32_t hash,const char* animation,uint32_t extra) {
    wardrobevoice::animation(hash,animation);
    updatenotice::animation(hash,animation);
    {std::lock_guard<std::recursive_mutex> guard(mutex);if(mousemenu::suppress(object,hash,animation,extra))return 0;}
    captionLayout=object;
    if(animation&&hash==0xd0805c2d&&!strcmp(animation,"stage_sele_base_out"))stageScreen=false;
    if(animation&&(!strcmp(animation,"cos_in_p1")||!strcmp(animation,"cos_in_p2"))){stageScreen=false;stageCaption.clear();}
    if(userconfig::current.flag("UI","enable_hide_battle_hud")) {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        battleHud.bind(reinterpret_cast<uintptr_t>(object));
        // Keep late animations from reviving a HUD while it is suppressed.
        if(battleHud.hidden&&BattleHudState::contains(hash))layoutHideOriginal(object,hash);
    }
    if(hash==rosterBase&&animation&&!strcmp(animation,"icon_pos_in")) {
        rosterBaseOwner=object;rosterBaseInstance=extra;
        log("UI ROSTER base position animation instance="+std::to_string(extra));
    }
    if(hash==Layer2Roster::portraits&&animation&&!strcmp(animation,"icon_in")) {
        rosterExitOwner=nullptr;rosterExitPose=false;
        if(rosterInstanceOwner!=object){rosterInstanceOwner=object;rosterInstances.clear();}
        if(std::find(rosterInstances.begin(),rosterInstances.end(),extra)==rosterInstances.end())rosterInstances.push_back(extra);
    }
    if(animation&&hash==Layer2Roster::portraits&&rosterFadeAt.load()) {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        auto start=rosterFadeAt.load();auto elapsed=start?GetTickCount64()-start:0;
        if(start&&(!strcmp(animation,"icon_on_p2")||!strcmp(animation,"icon_off_p2"))) {
            auto layout=reinterpret_cast<uintptr_t>(layoutObject(object,0,hash,extra));
            if(!strcmp(animation,"icon_on_p2"))rosterHover.enter(layout,elapsed);
            else rosterHover.leave(layout,elapsed);
            log(std::string("UI ROSTER HOVER ")+animation+" instance="+std::to_string(extra));
        }
        if(!strcmp(animation,"icon_select_p2")) {
            rosterFadeAt=0;rosterHover.begin(0);log("UI ROSTER fade ended: P2 selected");
        }
    }
    if(animation&&hash==0xb384f573&&!strcmp(animation,"cos_in_p2"))rosterFadeAt=0;
    // Finish before leaving the costume screen so no delayed request can restore
    // a stale preview after a menu transition. Natural requests cancel it too.
    if(animation&&!strcmp(animation,"cos_out_p1"))finishPreviewReload(0,true);
    if(animation&&!strcmp(animation,"cos_out_p2"))finishPreviewReload(1,true);
    if(animation&&!strcmp(animation,"detail_out")&&hairPlayer>=0)finishPreviewReload(static_cast<unsigned>(hairPlayer.load()),true);
    auto result=layoutOriginal(object,hash,animation,extra);
    {std::lock_guard<std::recursive_mutex> guard(mutex);mousemenu::animation(object,hash,animation,extra);}
    if(!animation)return result;
    if(userconfig::current.flag("UI","character_roster_transitions")&&roster.animation(hash,animation)) {
        // Only the confirmed P1 -> P2 handoff uses an opacity ramp. Returning
        // from Accessories still uses the native entrance transition below.
        const bool fade=userconfig::current.text("UI","roster_handoff")=="fade"&&!roster.hidden&&roster.accessoriesPlayer==0&&
            hash==Layer2Roster::portraits&&!strcmp(animation,"icon_on_p2")&&
            rosterInstanceOwner==object;
        rosterFadeAt=0;
        const bool nativeExit=userconfig::current.text("UI","roster_accessories_exit")=="native"&&roster.hidden&&rosterBaseOwner==object&&
            rosterInstanceOwner==object&&!rosterInstances.empty();
        const bool nativeReturn=userconfig::current.text("UI","roster_accessories_return")=="native"&&!roster.hidden&&rosterBaseOwner==object&&
            hash==0xb384f573&&(!strcmp(animation,"cos_in_p1")||!strcmp(animation,"cos_in_p2"));
        if(!roster.hidden) {
            rosterExitOwner=nullptr;
            if((rosterExitPose||nativeReturn)&&strcmp(animation,"icon_in")) {
                if(rosterBaseOwner==object)animationReset(object,rosterBase,"icon_pos_out",rosterBaseInstance);
                for(auto instance:rosterInstances)animationReset(object,Layer2Roster::portraits,"icon_out",instance);
                if(nativeReturn) {
                    animationReset(object,rosterBase,"icon_pos_in",rosterBaseInstance);
                    layoutOriginal(object,rosterBase,"icon_pos_in",rosterBaseInstance);
                    for(auto instance:rosterInstances) {
                        animationReset(object,Layer2Roster::portraits,"icon_in",instance);
                        layoutOriginal(object,Layer2Roster::portraits,"icon_in",instance);
                    }
                    log("UI ROSTER normal return from Accessories");
                } else log("UI ROSTER restored native exit start pose");
            }
            rosterExitPose=false;
        }
        if(fade) {
            std::lock_guard<std::recursive_mutex> guard(mutex);
            fadingRosterLayouts.clear();
            for(auto instance:rosterInstances)if(auto layout=layoutObject(object,0,Layer2Roster::portraits,instance))fadingRosterLayouts.push_back(layout);
            rosterHover.begin(reinterpret_cast<uintptr_t>(layoutObject(object,0,Layer2Roster::portraits,extra)));
            rosterFadeReads=0;rosterFadeAt=GetTickCount64();
            log("UI ROSTER opacity layouts="+std::to_string(fadingRosterLayouts.size()));
        }
        if(nativeExit) {
            rosterExitOwner=object;rosterExitThread=GetCurrentThreadId();rosterExitPose=true;
            layoutOriginal(object,rosterBase,"icon_pos_out",rosterBaseInstance);
            for(auto instance:rosterInstances)layoutOriginal(object,Layer2Roster::portraits,"icon_out",instance);
            log("UI ROSTER full native exit during Accessories P"+std::to_string(roster.accessoriesPlayer+1));
        } else (roster.hidden?layoutHideOriginal:layoutShowOriginal)(object,Layer2Roster::portraits);
        log(std::string("UI ROSTER ")+(roster.hidden?"HIDE ":nativeReturn?"NATIVE RETURN ":fade?"FADE IN ":"SHOW INSTANT ")+animation+" instances="+std::to_string(rosterInstances.size()));
    }
    if(userconfig::current.flag("Debug","log_ui_events")&&(layoutLogs++<400||hash==Layer2Roster::portraits||!strncmp(animation,"detail_",7)||!strncmp(animation,"cos_",4)))log("LAYER2 ANIMATION "+hex(hash)+" "+animation);
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
// Apply preview displacement to the native position input, never to saved data.
using WardrobePositionFn=void(*)(void*,const float*);
static WardrobePositionFn wardrobePositionOriginal=nullptr;
static void wardrobePositionHook(void* model,const float* position) {
    const float offset=mousemenu::verticalOffset.load();
    const auto owner=mousemenu::verticalOwner.load();
    if(owner && offset!=0 && mousemenu::wardrobePreview()) {
        // Only the root request at owner+0 receives the preview offset.
        // The other two models inherit its transform through attachment updates.
        // Translating those again separates the head from the body.
        for(unsigned part=2;part<3;++part) {
            uintptr_t request=0,current=0;
            if(mousemenu::read(owner+(2-part)*0x38,request) && request &&
               mousemenu::read(request+0x68,current) && current==reinterpret_cast<uintptr_t>(model)) {
                alignas(16) float moved[4];
                if(mousemenu::read(reinterpret_cast<uintptr_t>(position),moved)) {
                    moved[1]+=offset;wardrobePositionOriginal(model,moved);return;
                }
            }
        }
    }
    wardrobePositionOriginal(model,position);
}
static void modelDefaultsHook(void* unused,void* owner,uint8_t part) {
    bool changed=false;
    if(mousemenu::wardrobePreview())mousemenu::verticalOwner=reinterpret_cast<uintptr_t>(owner);
    if(owner && part<3) {
        // Native 22cbe80 maps parts 0/1/2 to shared requests at +70/+38/+0.
        // 22ca6e0 requires both +60 and +68 to be ready before rebuilding.
        auto request=*reinterpret_cast<BYTE**>(static_cast<BYTE*>(owner)+(2-part)*0x38);
        Layer2ModelSource source;
        if(request)source={reinterpret_cast<uintptr_t>(request),
            *reinterpret_cast<uintptr_t*>(request+0x60),*reinterpret_cast<uintptr_t*>(request+0x68)};
        std::lock_guard<std::recursive_mutex> guard(mutex);
        changed=modelSources.changed(reinterpret_cast<uintptr_t>(owner),part,source);
        // Bounded, read-only Wardrobe diagnostics: identify the model hierarchy
        // before introducing a preview-only translation control.
        if(changed && mousemenu::wardrobeOpen) {
            static unsigned wardrobeModelLogs=0;
            if(wardrobeModelLogs++<48) {
                std::ostringstream out;
                out<<"WARDROBE MODEL part="<<unsigned(part)<<std::hex
                   <<" owner="<<reinterpret_cast<uintptr_t>(owner)
                   <<" request="<<source.request<<" resource="<<source.resource
                   <<" model="<<source.model;
                log(out.str());
            }
        }
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
        if(!userconfig::current.flag("Layer2",hairMode?"enable_hair_cycling":"enable_costume_cycling"))return;
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
    if(animationpreviewtest::enabled&&player==0) {
        std::lock_guard<std::recursive_mutex> guard(mutex);
        animationpreviewtest::poll(mousemenu::wardrobePreview()&&!mousemenu::dialog&&!mousemenu::reward);
    }
    if(animationpreviewtest::pad(player,state,ret))return ret;
    haircolor::pad(player,state,ret);
    mousemenu::pad(player,state,ret);
    pumpHairColor();
    pumpPreviewReloads();
    static DWORD previous[4]{};
    if(ret==ERROR_SUCCESS&&player<4) {
        DWORD buttons=state->Gamepad.wButtons|(state->Gamepad.bLeftTrigger>128?0x10000:0);
        DWORD edge=buttons&~previous[player];previous[player]=buttons;
        if(edge&XINPUT_GAMEPAD_B){rosterBackAt=GetTickCount64();rosterFadeAt=0;}
        if(userconfig::current.flag("Layer2","gamepad_controls")) {
            if(edge&XINPUT_GAMEPAD_BACK)cycle(-1,"Select/Back");
            else if(edge&0x10000)cycle(1,"L2/LT");
        }
    }
    return ret;
}
static void battleHudInput(bool down) {
    std::lock_guard<std::recursive_mutex> guard(mutex);
    if(!battleHud.input(down,userconfig::current.flag("UI","enable_hide_battle_hud")))return;
    unsigned changed=0;
    if(battleHud.owner) {
        auto object=reinterpret_cast<void*>(battleHud.owner);
        for(auto hash:battleHudLayouts) {
            if(battleHud.hidden){layoutHideOriginal(object,hash);++changed;}
            else if(battleHud.restore(hash)){layoutShowOriginal(object,hash);++changed;}
        }
    }
    log(std::string("UI BATTLE HUD ")+(battleHud.hidden?"HIDDEN":"SHOWN")+" via F5; groups="+std::to_string(changed));
}
static HRESULT WINAPI keyboardHook(void* device,DWORD length,void* buffer) {
    using Fn=HRESULT(WINAPI*)(void*,DWORD,void*);
    auto original=reinterpret_cast<Fn>((*reinterpret_cast<void***>(device))[9]);
    HRESULT result=original(device,length,buffer);
    pumpPreviewReloads();
    static bool previous=false;
    if(SUCCEEDED(result)&&length==256) {
        auto keys=static_cast<unsigned char*>(buffer);
        mousemenu::keyboard(keys);
        haircolor::keyboard(keys);
        pumpHairColor();
        battleHudInput((keys[0x3f]&0x80)!=0);
        if(userconfig::current.flag("UI","enable_hide_battle_hud"))keys[0x3f]=0;
        if((static_cast<unsigned char*>(buffer)[0x01]&0x80)!=0){rosterBackAt=GetTickCount64();rosterFadeAt=0;}
        bool down=(static_cast<unsigned char*>(buffer)[0x21]&0x80)!=0;
        bool edge=down&&!previous;previous=down;if(edge&&userconfig::current.flag("Layer2","keyboard_controls"))cycle(1,"F");
    }
    if(FAILED(result))battleHudInput(false);
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
    if(userconfig::current.has("Branding","enabled"))on=userconfig::current.flag("Branding","enabled");
    if(!on)return L"";
    auto label=wide(name+(version.empty()?"":" "+version));
    label.erase(std::remove_if(label.begin(),label.end(),[](wchar_t c){return c<32;}),label.end());
    return label;
}
static void titleTextHook(void* object,uintptr_t unused,uint32_t pane,uint32_t index,uint32_t type,const wchar_t* text,uint32_t length) {
    auto updateText=updatenotice::replacement(pane,text,length);
    if(!updateText.empty()){
        if(!updatenotice::developerPage&&updateText!=L"Don't show again until next game update"&&updateText!=L"Close"){
            updatenotice::capture(titleTextOriginal,object,unused,index,type,updateText);
            updateText=updatenotice::colorBrackets(noticescroll::frame(updateText,0,updatenotice::scrollInterval,updatenotice::scrollLines,updatenotice::scrollEnabled),false);
        }
        titleTextOriginal(object,unused,pane,index,type,updateText.c_str(),static_cast<uint32_t>(updateText.size()));return;
    }
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
    layoutObject=reinterpret_cast<LayoutObjectFn>(gamecode::get("layoutObject"));
    animationReset=reinterpret_cast<AnimationResetFn>(gamecode::get("animationReset"));
    animationPlaying=reinterpret_cast<AnimationPlayingFn>(gamecode::get("animationPlaying"));
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
        {gamecode::get("rosterColor"),bytes("48 89 5c 24 08 57 48 83 ec 20 48 8b f9 8b da"),(void*)rosterColorHook,(void**)&rosterColorOriginal},
        {gamecode::get("layoutShow"),bytes("48 89 5c 24 08 89 54 24 10 57 48 83 ec 20"),(void*)layoutShowHook,(void**)&layoutShowOriginal},
        {gamecode::get("layoutHide"),bytes("48 89 5c 24 08 89 54 24 10 57 48 83 ec 20"),(void*)layoutHideHook,(void**)&layoutHideOriginal},
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
    for(const auto& mod:mods)if(mod.privateRoute.enabled) {
        for(const auto& pair:mod.privateRoute.aliases){
            auto prior=privateCompanionSources.emplace(pair.second,pair.first);
            if(!prior.second&&prior.first->second!=pair.first)throw std::runtime_error("Conflicting private model aliases");
            privateHairModels.insert(pair.second);
        }
        if(mod.privateRoute.work[2]&&mod.privateRoute.source[2])privateHairModels.insert(mod.privateRoute.work[2]);
        for(unsigned part=0;part<3;++part) {
            auto work=mod.privateRoute.work[part],source=mod.privateRoute.source[part];
            if(!work||!source||work==source)continue;
            auto prior=privateCompanionSources.emplace(work,source);
            if(!prior.second&&prior.first->second!=source)throw std::runtime_error("Conflicting private model companion aliases");
        }
    }
    if(!privateCompanionSources.empty()) {
        auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
        auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
        auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);BYTE* found=nullptr;
        for(unsigned i=0;i<dir.Size/sizeof(*fs);++i) {
            auto f=fs[i];
            if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.EndAddress-f.BeginAddress!=privateCompanionPattern.size)continue;
            if(!gamecode::match(base+f.BeginAddress,privateCompanionPattern))continue;
            if(found)throw std::runtime_error("Ambiguous private companion resolver");
            found=base+f.BeginAddress;
        }
        if(!found)throw std::runtime_error("Private companion resolver unavailable");
        hooks.push_back({found,bytes("48 89 5c 24 08 48 89 74 24 10 57 48 83 ec 20"),(void*)companionHook,(void**)&companionOriginal});
        log("LAYER2 PRIVATE companion resolver rva="+hex(static_cast<uint32_t>(found-base)));
        found=nullptr;
        for(unsigned i=0;i<dir.Size/sizeof(*fs);++i) {
            auto f=fs[i];
            if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.EndAddress-f.BeginAddress!=privateBattlePattern.size)continue;
            if(!gamecode::match(base+f.BeginAddress,privateBattlePattern))continue;
            if(found)throw std::runtime_error("Ambiguous private battle owner");
            found=base+f.BeginAddress;
        }
        if(!found)throw std::runtime_error("Private battle owner unavailable");
        hooks.push_back({found,bytes("48 8b c4 44 88 48 20 48 89 48 08 57 48 83 ec 70"),(void*)battleOwnerHook,(void**)&battleOwnerOriginal});
        log("LAYER2 PRIVATE battle owner rva="+hex(static_cast<uint32_t>(found-base)));
    }
    if(GetFileAttributesW((gameRoot+L"REDELBE_LR\\animation_trace.enabled").c_str())!=INVALID_FILE_ATTRIBUTES) {
        auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
        auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
        auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);
        for(unsigned kind=0;kind<3;++kind){
            const auto& pattern=kind==2?animationActionPattern:kind?animationCameraPattern:animationModelPattern;BYTE* found=nullptr;bool ambiguous=false;
            for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.EndAddress-f.BeginAddress!=pattern.size)continue;if(!gamecode::match(base+f.BeginAddress,pattern))continue;if(found){ambiguous=true;break;}found=base+f.BeginAddress;}
            if(!found||ambiguous){log("ANIMATION TRACE unavailable; no hook installed");continue;}
            hooks.push_back({found,bytes(kind==2?"48 89 5c 24 18 55 56 57 41 54 41 57 48 8d ac 24 10 fe ff ff":kind?"48 89 5c 24 10 48 89 6c 24 18 56 57 41 56 48 81 ec c0 00 00 00":"48 89 5c 24 20 55 56 57 41 56 41 57 48 8d ac 24 40 ff ff ff"),kind==2?(void*)animationtrace::actionHook:kind?(void*)animationtrace::cameraHook:(void*)animationtrace::modelHook,kind==2?(void**)&animationtrace::actionOriginal:kind?(void**)&animationtrace::cameraOriginal:(void**)&animationtrace::modelOriginal});
            log("ANIMATION TRACE resolved "+std::string(pattern.name));
        }
    }
    animationtrace::evaluationTracing=GetFileAttributesW((gameRoot+L"REDELBE_LR\\animation_evaluator_trace.enabled").c_str())!=INVALID_FILE_ATTRIBUTES;
    if(userconfig::current.flag("AnimationBrowser","enabled")||animationtrace::evaluationTracing) {
        animationpreviewtest::initialize();
        victoryobserver::initialize();
        auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
        auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
        auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);
        auto signature=bytes("48 8b c4 57 48 81 ec b0 00 00 00 0f 29 78 b8 0f 28 fb 48 89 58 10 48 8b d9 48 89 68 18 49 8b e8 48 89 70 20 4c 89 60 f0 4c 89 68 e8 4c 89 70 e0");
        BYTE* found=nullptr;bool ambiguous=false;
        for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.BeginAddress+signature.size()>nt->OptionalHeader.SizeOfImage)continue;if(memcmp(base+f.BeginAddress,signature.data(),signature.size()))continue;if(found){ambiguous=true;break;}found=base+f.BeginAddress;}
        if(found&&!ambiguous){animationpreviewtest::enabled=true;hooks.push_back({found,bytes("48 8b c4 57 48 81 ec b0 00 00 00 0f 29 78 b8"),(void*)animationtrace::evaluateHook,(void**)&animationtrace::evaluateOriginal});log("ANIMATION EVALUATE resolved rva="+hex(static_cast<uint32_t>(found-base)));}
        else log("ANIMATION EVALUATE unavailable; no hook installed");

        {
            auto directSignature=bytes("4c 8b dc 49 89 5b 08 49 89 6b 10 49 89 73 18 57 41 56 41 57 48 83 ec 60 4c 8b b4 24 a0 00 00 00 45 33 d2");
            BYTE* directFound=nullptr;bool directAmbiguous=false;
            for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.BeginAddress+directSignature.size()>nt->OptionalHeader.SizeOfImage)continue;if(memcmp(base+f.BeginAddress,directSignature.data(),directSignature.size()))continue;if(directFound){directAmbiguous=true;break;}directFound=base+f.BeginAddress;}
            if(directFound&&!directAmbiguous){hooks.push_back({directFound,bytes("4c 8b dc 49 89 5b 08 49 89 6b 10 49 89 73 18"),(void*)animationtrace::evaluateDirectHook,(void**)&animationtrace::evaluateDirectOriginal});log("ANIMATION DIRECT facial playback resolved rva="+hex(static_cast<uint32_t>(directFound-base)));}
        }

        {
            auto resourceSignature=bytes("48 8b c4 4c 89 40 18 48 89 50 10 55 57 41 55 41 56 48 8d 68 b8 48 81 ec 28 01 00 00 0f 29 70 b8 4d 8b e8");
            BYTE* resourceFound=nullptr;bool resourceAmbiguous=false;
            for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.BeginAddress+resourceSignature.size()>nt->OptionalHeader.SizeOfImage)continue;if(memcmp(base+f.BeginAddress,resourceSignature.data(),resourceSignature.size()))continue;if(resourceFound){resourceAmbiguous=true;break;}resourceFound=base+f.BeginAddress;}
            if(resourceFound&&!resourceAmbiguous){hooks.push_back({resourceFound,bytes("48 8b c4 4c 89 40 18 48 89 50 10 55 57 41 55"),(void*)animationtrace::evaluateResourceHook,(void**)&animationtrace::evaluateResourceOriginal});log("ANIMATION RESOURCE resolved rva="+hex(static_cast<uint32_t>(resourceFound-base)));}
        }
        if(GetFileAttributesW((gameRoot+L"REDELBE_LR\\facial_compositor_test.enabled").c_str())!=INVALID_FILE_ATTRIBUTES){
            auto signature=bytes("48 8b c4 48 89 58 08 48 89 70 10 48 89 78 18 4c 89 60 20 55 41 56 41 57 48 8d 6c 24 80 48 81 ec 80 01 00 00 0f 29 70 d8 0f 28 f2 44 0f 29 48 a8 45 8b f1");
            BYTE* found=nullptr;bool ambiguous=false;
            for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress-f.BeginAddress<signature.size())continue;if(memcmp(base+f.BeginAddress,signature.data(),signature.size()))continue;if(found){ambiguous=true;break;}found=base+f.BeginAddress;}
            if(found&&!ambiguous){hooks.push_back({found,bytes("48 8b c4 48 89 58 08 48 89 70 10 48 89 78 18"),(void*)animationtrace::faceBoneHook,(void**)&animationtrace::faceBoneOriginal});log("FACIAL COMPOSITOR resolved rva="+hex(static_cast<uint32_t>(found-base)));}
            else log("FACIAL COMPOSITOR unavailable: signature not unique");
        }
        animationtrace::nativeCameraTracing=GetFileAttributesW((gameRoot+L"REDELBE_LR\\native_camera_trace.enabled").c_str())!=INVALID_FILE_ATTRIBUTES;
        {
            const char* cameraSignatures[]={
                "48 89 5c 24 08 57 48 83 ec 20 48 8b da 48 8b f9",
                "48 89 5c 24 10 57 48 81 ec c0 00 00 00 0f 29 b4 24 b0 00 00 00",
                "48 89 5c 24 08 57 48 83 ec 20 48 8b da 48 8b f9",
                "48 8b c4 48 89 58 20 f3 0f 11 50 18 55 56 57 48 8d 68 b8 48 81 ec 30 01 00 00 0f 29 70 d8"};
            unsigned cameraResolved=0;
            for(int kind=0;kind<4;++kind){
                auto prologue=bytes(cameraSignatures[kind]);BYTE* target=nullptr;bool multiple=false;
                for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){
                    auto rva=fs[i].BeginAddress;
                    if(rva+0x60>nt->OptionalHeader.SizeOfImage||memcmp(base+rva,prologue.data(),prologue.size()))continue;
                    // Verify the camera-specific body as well as the common prologue.
                    auto discriminator=bytes(kind==3?"0f 28 ca 48 8b 01 49 8b f1":kind==2?"48 8b d3 48 8b cf e8":kind==1?"48 8b 5b 20 48 8b cb 48 8b 03 ff 50 20":"48 8d 97 d0 2e 00 00 48 8b cb");
                    size_t offset=kind==3?0x1e:kind==1?0x35:0x15;
                    if(memcmp(base+rva+offset,discriminator.data(),discriminator.size()))continue;
                    if(kind==2){
                        auto callee=int64_t(rva)+0x20+*reinterpret_cast<int32_t*>(base+rva+0x1c);
                        auto body=bytes("48 8b c4 48 89 58 18 48 89 70 20 55 57 41 56 48 8d 68 a1 48 81 ec a0 00 00 00 0f 29 70 d8");
                        if(callee<0||uint64_t(callee)+body.size()>nt->OptionalHeader.SizeOfImage||memcmp(base+callee,body.data(),body.size()))continue;
                    }
                    if(target){multiple=true;break;}target=base+rva;
                }
                if(target&&!multiple){
                    if(kind==3)animationpreviewtest::camera::evaluate=reinterpret_cast<animationpreviewtest::camera::Evaluate>(target);
                    else if(kind||animationtrace::nativeCameraTracing)hooks.push_back({target,prologue,kind==2?(void*)animationtrace::nativeCameraCommitHook:kind?(void*)animationtrace::nativeCameraMotionHook:(void*)animationtrace::nativeCameraStateHook,kind==2?(void**)&animationtrace::nativeCameraCommitOriginal:kind?(void**)&animationtrace::nativeCameraMotionOriginal:(void**)&animationtrace::nativeCameraStateOriginal});
                    cameraResolved|=1u<<kind;
                    log("NATIVE CAMERA resolved kind="+std::to_string(kind)+" rva="+hex(static_cast<uint32_t>(target-base)));
                }else log("NATIVE CAMERA trace unavailable kind="+std::to_string(kind));
            }
            animationpreviewtest::camera::available=(cameraResolved&14)==14;
        }
    }
    BYTE* privateHairCall=nullptr;
    if(!privateHairModels.empty()) {
        privateHairCall=gamecode::get("request")+0xb0;
        auto fn=gamecode::callTarget(privateHairCall);
        auto prologue=bytes("40 53 48 83 ec 20 8b d9 48 8d 0d");
        if(memcmp(fn,prologue.data(),prologue.size()))throw std::runtime_error("Private hair canonicalizer mismatch");
        privateHairOriginal=reinterpret_cast<PrivateHairFn>(fn);
    }
    // Optional Wardrobe position setter. Resolve at function boundaries and
    // require a unique signature; unfamiliar builds retain ordinary rotation.
    {
        auto signature=bytes("48 89 5c 24 08 48 89 74 24 10 57 48 81 ec d0 00 00 00 48 8b b1 c0 01 00 00 48 8b fa 0f 29 b4 24 c0 00 00 00 48 8b d9");
        auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
        auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
        auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);BYTE* found=nullptr;unsigned matches=0;
        for(unsigned i=0;i<dir.Size/sizeof(*fs);++i) {
            auto f=fs[i];
            if(f.EndAddress<=nt->OptionalHeader.SizeOfImage && f.EndAddress>=f.BeginAddress+signature.size() &&
               !memcmp(base+f.BeginAddress,signature.data(),signature.size())){found=base+f.BeginAddress;++matches;}
        }
        if(matches==1){hooks.push_back({found,bytes("48 89 5c 24 08 48 89 74 24 10 57 48 81 ec d0 00 00 00"),(void*)wardrobePositionHook,(void**)&wardrobePositionOriginal});log("WARDROBE vertical position hook resolved");}
        else log("WARDROBE vertical position unavailable: signature not unique");
    }
    // Optional persistence hook: resolve the complete getter, never guess an RVA.
    {
        auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
        auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
        auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);BYTE* found=nullptr;bool ambiguous=false;
        for(unsigned i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.EndAddress<=nt->OptionalHeader.SizeOfImage&&f.EndAddress-f.BeginAddress==hairSlotPattern.size&&gamecode::match(base+f.BeginAddress,hairSlotPattern)){if(found)ambiguous=true;found=base+f.BeginAddress;}}
        if(found&&!ambiguous)hooks.push_back({found,bytes("48 89 5c 24 08 48 89 74 24 10 57 48 83 ec 20"),(void*)haircolor::hairSlotHook,(void**)&haircolor::hairSlotOriginal});
        else log("HAIR COLOR slot tracking unavailable: getter pattern not unique");
    }
    if(userconfig::current.flag("Misc","slot_info_in_sss")) {
        // Optional: an unfamiliar texture setter disables only stage captions.
        try {
            auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
            auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
            auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);BYTE* found=nullptr;
            for(unsigned i=0;i<dir.Size/sizeof(*fs);++i) {
                auto& f=fs[i];
                if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.EndAddress-f.BeginAddress!=stageTexturePattern.size)continue;
                if(!gamecode::match(base+f.BeginAddress,stageTexturePattern))continue;
                if(found)throw std::runtime_error("ambiguous texture setter");found=base+f.BeginAddress;
            }
            if(!found)throw std::runtime_error("unrecognized texture setter");
            auto expected=bytes("40 55 56 57 41 54 41 55 41 56 41 57 48 8d 6c 24 e9");
            if(memcmp(found,expected.data(),expected.size()))throw std::runtime_error("texture prologue mismatch");
            hooks.push_back({found,expected,(void*)stageTextureHook,(void**)&stageTextureOriginal});
            log("STAGE CAPTION pattern rva="+hex(static_cast<uint32_t>(found-base)));
        } catch(const std::exception& e){log(std::string("STAGE CAPTION unavailable: ")+e.what());}
    }
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
    BYTE* privateHairRelay=nullptr;
    if(privateHairCall) {
        privateHairRelay=allocateNear(privateHairCall);absoluteJump(privateHairRelay,(void*)privateHairHook);
        DWORD prior;VirtualProtect(privateHairRelay,0x1000,PAGE_EXECUTE_READ,&prior);
    }
    BYTE* relay=allocateNear(keyboard);absoluteJump(relay,(void*)keyboardHook);DWORD old;VirtualProtect(relay,0x1000,PAGE_EXECUTE_READ,&old);
    // ASI startup runs before selection code. Install only after every signature passes.
    for(auto& hook:hooks){std::vector<BYTE> patch(hook.expected.size(),0x90);absoluteJump(patch.data(),hook.replacement);write(hook.target,patch.data(),patch.size());}
    if(privateHairCall) {
        BYTE patch[5]={0xe8,0,0,0,0};auto delta=static_cast<int32_t>(privateHairRelay-(privateHairCall+5));
        memcpy(patch+1,&delta,4);write(privateHairCall,patch,sizeof(patch));
        log("LAYER2 PRIVATE hairstyle model identities preserved");
    }
    BYTE call[6]={0x90,0xe8,0,0,0,0};int32_t displacement=static_cast<int32_t>(relay-(keyboard+6));memcpy(call+2,&displacement,4);write(keyboard,call,6);
    auto cell=gamecode::xinputCell(base);
    xinputOriginal=reinterpret_cast<decltype(xinputOriginal)>(*cell);
    void* replacement=(void*)xinputHook;write(reinterpret_cast<BYTE*>(cell),reinterpret_cast<BYTE*>(&replacement),sizeof(replacement));
    log("LAYER2 installed model/layout/four-cache/model-defaults/keyboard/XInput hooks; Default selected for every player/slot");
}
}

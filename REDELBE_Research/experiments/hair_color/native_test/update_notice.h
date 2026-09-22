#pragma once
#include "notice_scroll.h"
namespace updatenotice {
static bool opened=false,developerPage=false,inWindow=false,confirmed=false,automatic=false;
static ULONGLONG menuAt=0,pulseUntil=0,followAt=0;
static std::wstring gameVersion;
using TextSetter=void(*)(void*,uintptr_t,uint32_t,uint32_t,uint32_t,const wchar_t*,uint32_t);
static TextSetter textSetter=nullptr;
static void* textObject=nullptr;
static uintptr_t textUnused=0;
static uint32_t textIndex=0,textType=0;
static std::wstring plainNotice;
static ULONGLONG nextColorAt=0;
static bool yellow=false;
static std::atomic<bool> smoothReady{false};
static bool nativeCleared=false;
static ULONGLONG scrollStarted=0;
static unsigned scrollInterval=1800,scrollLines=7;
static bool scrollEnabled=true;
static std::wstring colorBrackets(const std::wstring& text,bool useYellow){
    std::wstring result;size_t pos=0;
    while(pos<text.size()){
        auto begin=text.find(L'[',pos);
        if(begin==std::wstring::npos){result+=text.substr(pos);break;}
        auto end=text.find(L']',begin+1);
        if(end==std::wstring::npos){result+=text.substr(pos);break;}
        result+=text.substr(pos,begin-pos);
        result+=useYellow?L"^00~YELLOW~":L"^00~GREEN~";
        result+=text.substr(begin,end-begin+1);result+=L"^00~DEFAULT~";pos=end+1;
    }
    return result;
}
static void capture(TextSetter setter,void* object,uintptr_t unused,uint32_t index,uint32_t type,const std::wstring& text){
    textSetter=setter;textObject=object;textUnused=unused;textIndex=index;textType=type;
    plainNotice=text;yellow=false;nextColorAt=GetTickCount64()+700;
    nativeCleared=false;
    scrollStarted=GetTickCount64();auto path=gameRoot+L"REDELBE_LR\\update_info.ini";
    scrollEnabled=GetPrivateProfileIntW(L"UpdateInfo",L"AutoScroll",1,path.c_str())!=0;
    scrollInterval=std::max(300u,std::min(10000u,GetPrivateProfileIntW(L"UpdateInfo",L"ScrollIntervalMs",1800,path.c_str())));
    scrollLines=std::max(2u,std::min(12u,GetPrivateProfileIntW(L"UpdateInfo",L"VisibleLines",7,path.c_str())));
}
static void animateColor(){
    if(!inWindow||developerPage||!textObject||!textSetter||plainNotice.empty())return;
    if(smoothReady&&scrollEnabled){if(!nativeCleared){textSetter(textObject,textUnused,0xdf867d44,textIndex,textType,L"",0);nativeCleared=true;}return;}
    auto now=GetTickCount64();if(now<nextColorAt)return;
    nextColorAt=now+700;yellow=!yellow;
    auto colored=colorBrackets(noticescroll::frame(plainNotice,now-scrollStarted,scrollInterval,scrollLines,scrollEnabled),yellow);
    textSetter(textObject,textUnused,0xdf867d44,textIndex,textType,colored.c_str(),static_cast<uint32_t>(colored.size()));
}
static WORD previousButtons=0;
static bool closeRequested=false,saveRequested=false;
static WORD buttons(WORD value){
    WORD edge=value&~previousButtons;previousButtons=value;
    if(!inWindow)return value;
    if(closeRequested)return value&~(XINPUT_GAMEPAD_A|XINPUT_GAMEPAD_B);
    if(edge&XINPUT_GAMEPAD_B){closeRequested=true;saveRequested=false;log("UPDATE INFO Back: close without saving");return (value&~XINPUT_GAMEPAD_B)|XINPUT_GAMEPAD_A;}
    if(edge&XINPUT_GAMEPAD_A){closeRequested=true;saveRequested=true;}
    return value;
}
static std::wstring statePath(){return gameRoot+L"REDELBE_LR\\update_info_state.ini";}
static std::wstring message(){
    std::ifstream file(gameRoot+L"REDELBE_LR\\update_info.txt",std::ios::binary);
    std::string data;char buffer[16385];file.read(buffer,sizeof(buffer));
    if(file.gcount()>16384)return L"";
    data.assign(buffer,static_cast<size_t>(file.gcount()));
    if(data.compare(0,3,"\xef\xbb\xbf")==0)data.erase(0,3);
    return wide(data);
}
static bool hidden(bool dev){
    if(!dev&&!birthdays::heading.empty())return false;
    wchar_t saved[128]{};
    GetPrivateProfileStringW(L"Dismissed",dev?L"DeveloperGame":L"RedelbeGame",L"",saved,128,statePath().c_str());
    if(gameVersion.empty()||gameVersion!=saved)return false;
    if(!dev){
        std::string digest;if(!sha256(gameRoot+L"REDELBE_LR\\update_info.txt",digest))return false;
        GetPrivateProfileStringW(L"Dismissed",L"RedelbeNotes",L"",saved,128,statePath().c_str());
        if(wide(digest)!=saved)return false;
    }
    return true;
}
static void remember(){
    if(gameVersion.empty())return;
    bool ok=WritePrivateProfileStringW(L"Dismissed",developerPage?L"DeveloperGame":L"RedelbeGame",gameVersion.c_str(),statePath().c_str())!=FALSE;
    if(!developerPage){std::string digest;if(sha256(gameRoot+L"REDELBE_LR\\update_info.txt",digest))ok=WritePrivateProfileStringW(L"Dismissed",L"RedelbeNotes",wide(digest).c_str(),statePath().c_str())&&ok;}
    log(ok?"UPDATE INFO dismissal saved":"UPDATE INFO dismissal save failed");
}
static bool everyLaunch(){return GetPrivateProfileIntW(L"UpdateInfo",L"ShowEveryLaunch",1,(gameRoot+L"REDELBE_LR\\update_info.ini").c_str())!=0;}
static void animation(uint32_t hash,const char* name){
    if(!name)return;
    if(hash==0x84b536e1&&!strcmp(name,"menu_in")&&!opened){menuAt=GetTickCount64();developerPage=(message().empty()&&birthdays::heading.empty());}
    if(hash!=0xdf867d44)return;
    if(!strcmp(name,"in")){opened=true;inWindow=true;confirmed=false;closeRequested=false;saveRequested=false;pulseUntil=0;log(developerPage?"UPDATE INFO developer page":"UPDATE INFO REDELBE page");}
    if(!strcmp(name,"eff_select")&&inWindow)confirmed=saveRequested;
    if(!strcmp(name,"out")&&inWindow){
        inWindow=false;textObject=nullptr;plainNotice.clear();if(confirmed&&(developerPage||birthdays::heading.empty()))remember();confirmed=false;
        if(!developerPage&&(!automatic||!hidden(true))){developerPage=true;followAt=GetTickCount64()+450;}
        else {developerPage=(message().empty()&&birthdays::heading.empty());followAt=0;automatic=false;}
    }
}
static std::wstring replacement(uint32_t pane,const wchar_t* text,uint32_t length){
    if(pane!=0xdf867d44||!text||!length||length>32768)return L"";
    std::wstring original(text,length);while(!original.empty()&&original.back()==0)original.pop_back();
    if(original==L"Close"&&!developerPage&&!birthdays::heading.empty())return L"Close";
    if(original==L"Close")return L"Don't show again until next game update";
    if(!developerPage&&original.find(L"[Update Info]")!=std::wstring::npos){
        auto custom=message();if(!birthdays::heading.empty())custom=L"\n\n\n\n"+(birthdays::specialMessage.empty()?birthdays::heading:birthdays::specialMessage)+L"\n\n"+custom; if(!custom.empty())custom+=L"\n\nBack: close without saving this preference.";
        return custom;
    }
    return L"";
}
static WORD input(bool mainMenu){
    auto now=GetTickCount64();
    if(pulseUntil){if(now<pulseUntil)return XINPUT_GAMEPAD_RIGHT_THUMB;pulseUntil=0;}
    if(followAt&&now>=followAt&&!inWindow){followAt=0;pulseUntil=now+80;return XINPUT_GAMEPAD_RIGHT_THUMB;}
    if(opened||!mainMenu||!menuAt||now-menuAt<1500)return 0;
    opened=true;
    if((!everyLaunch()&&birthdays::heading.empty())||(hidden(false)&&hidden(true)))return 0;
    automatic=true;developerPage=hidden(false)||(message().empty()&&birthdays::heading.empty());
    pulseUntil=now+80;log("UPDATE INFO automatic launch request");return XINPUT_GAMEPAD_RIGHT_THUMB;
}
}

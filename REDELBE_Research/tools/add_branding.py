from pathlib import Path
p=Path('tools/generate_patterns.py');s=p.read_text();s=s.replace("targets={'caption':", "targets={'titleText':0x21c1df0,'caption':");p.write_text(s)
p=Path('prototype/layer2_runtime.h');s=p.read_text();pos=s.index('static void install() {');s=s[:pos]+'''// The native UTF-16 pane setter copies its input synchronously.
using TitleTextFn=void(*)(void*,uintptr_t,uint32_t,uint32_t,uint32_t,const wchar_t*,uint32_t);
static TitleTextFn titleTextOriginal;
static bool isVersionText(const wchar_t* text,uint32_t length) {
    if(!text||length<4||length>24)return false;
    uint32_t n=length;if(text[n-1]==0)--n;
    uint32_t i=0;
    if(n>4&&!wcsncmp(text,L"Ver.",4))i=4;
    else if(text[0]==L'v'||text[0]==L'V')i=1;
    else return false;
    while(i<n&&text[i]==L' ')++i;
    bool dot=false,digit=false;
    for(;i<n;++i){if(text[i]>=L'0'&&text[i]<=L'9'){digit=true;continue;}if(text[i]==L'.'&&digit){dot=true;digit=false;continue;}return false;}
    return dot&&digit;
}
static std::wstring brandingLabel() {
    std::wstring path=gameRoot+L"REDELBE_LR\\\\branding.ini";
    if(GetFileAttributesW(path.c_str())==INVALID_FILE_ATTRIBUTES) {
        HANDLE f=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(f!=INVALID_HANDLE_VALUE){const char* data="; UTF-8. Edit Name and Version, then return to the title screen or restart.\\r\\n[Branding]\\r\\nEnabled=1\\r\\nName=Raikiri\\r\\nVersion=0.3 RC3\\r\\n";DWORD count;WriteFile(f,data,(DWORD)strlen(data),&count,nullptr);CloseHandle(f);}
    }
    std::ifstream in(path);std::string line,name="Raikiri",version="0.3 RC3";bool on=true,section=false;
    while(std::getline(in,line)) {
        if(line.size()>=3&&line.compare(0,3,"\\xef\\xbb\\xbf")==0)line.erase(0,3);
        if(!line.empty()&&line.back()=='\\r')line.pop_back();
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
    if(isVersionText(text,length)) {
        auto label=brandingLabel();
        if(!label.empty()) {
            size_t n=length;if(text[n-1]==0)--n;
            std::wstring combined(text,n);combined+=L"  ";combined+=label;
            log("TITLE BRANDING pane="+hex(pane)+" text="+utf8(combined));
            titleTextOriginal(object,unused,pane,index,type,combined.c_str(),static_cast<uint32_t>(combined.size()));return;
        }
    }
    titleTextOriginal(object,unused,pane,index,type,text,length);
}
''' +s[pos:];s=s.replace('std::vector<Hook> hooks={','std::vector<Hook> hooks={\n        {gamecode::get("titleText"),bytes("48 89 5c 24 08 48 89 74 24 10 57 48 83 ec 20"),(void*)titleTextHook,(void**)&titleTextOriginal},');p.write_text(s)
p=Path('prototype/loader.cpp');p.write_text(p.read_text().replace('0.3 RC2','0.3 RC3'))

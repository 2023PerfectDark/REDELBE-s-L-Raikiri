#pragma once
#include "game_patterns_data.h"
#include <stdexcept>
#include <cstring>
namespace gamecode {
static std::map<std::string,BYTE*> resolved;
static bool match(const BYTE* p,const GamePattern& s) {
    for(unsigned i=0;i<s.size;++i)if(s.mask[i] && p[i]!=static_cast<unsigned char>(s.data[i]))return false;
    return true;
}
static BYTE* get(const char* name) {
    auto it=resolved.find(name);if(it==resolved.end())throw std::runtime_error(std::string("Missing game pattern: ")+name);return it->second;
}
static BYTE* callTarget(BYTE* instruction) {
    if(*instruction!=0xe8)throw std::runtime_error("Expected native call instruction");
    int32_t delta;memcpy(&delta,instruction+1,4);return instruction+5+delta;
}
static void resolve(BYTE* base) {
    resolved.clear();auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE)throw std::runtime_error("Invalid executable header");
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+dos->e_lfanew);
    if(nt->Signature!=IMAGE_NT_SIGNATURE||nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64)throw std::runtime_error("Expected x64 executable");
    auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
    if(!dir.Size||dir.Size%sizeof(RUNTIME_FUNCTION)||static_cast<uint64_t>(dir.VirtualAddress)+dir.Size>nt->OptionalHeader.SizeOfImage)throw std::runtime_error("Invalid native function table");
    auto functions=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);
    for(const auto& pattern:gamePatterns) {
        if(!strcmp(pattern.name,"release"))continue; // Resolved from the verified request call below.
        BYTE* found=nullptr;
        for(unsigned i=0;i<dir.Size/sizeof(RUNTIME_FUNCTION);++i) {
            const auto& f=functions[i];
            if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.EndAddress-f.BeginAddress!=pattern.size)continue;
            if(!match(base+f.BeginAddress,pattern))continue;
            if(found)throw std::runtime_error(std::string("Ambiguous game pattern: ")+pattern.name);
            found=base+f.BeginAddress;
        }
        if(!found)throw std::runtime_error(std::string("Unsupported game code: ")+pattern.name);
        resolved[pattern.name]=found+pattern.offset;
    }
    auto release=callTarget(get("request")+0x167);
    bool valid=false;
    for(const auto& p:gamePatterns)if(!strcmp(p.name,"release")) {
        if(release>=base && release<=base+nt->OptionalHeader.SizeOfImage-p.size)valid=match(release,p);
    }
    if(!valid)throw std::runtime_error("Body release call target mismatch");resolved["release"]=release;
    // Verify the relationships used for async model refresh, not just prologues.
    if(callTarget(get("defaults")+0xec)!=get("cache0") ||
       callTarget(get("scale")+0x132)!=get("cache0") ||
       callTarget(get("scale")+0x169)!=get("defaults"))throw std::runtime_error("Model initialization call graph changed");
    if(callTarget(get("randomCaller1")-5)!=get("random") ||
       callTarget(get("randomCaller2")-5)!=get("random"))throw std::runtime_error("Random selection call graph changed");
}
static void** xinputCell(BYTE* base) {
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
    auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];void** result=nullptr;
    for(auto d=reinterpret_cast<IMAGE_IMPORT_DESCRIPTOR*>(base+dir.VirtualAddress);d->Name;++d) {
        std::string dll=reinterpret_cast<char*>(base+d->Name);
        std::transform(dll.begin(),dll.end(),dll.begin(),[](unsigned char c){return static_cast<char>(tolower(c));});
        if(dll.find("xinput")==std::string::npos||!d->OriginalFirstThunk)continue;
        auto names=reinterpret_cast<IMAGE_THUNK_DATA64*>(base+d->OriginalFirstThunk);
        auto slots=reinterpret_cast<IMAGE_THUNK_DATA64*>(base+d->FirstThunk);
        for(;names->u1.AddressOfData;++names,++slots) {
            if(IMAGE_SNAP_BY_ORDINAL64(names->u1.Ordinal))continue;
            auto name=reinterpret_cast<IMAGE_IMPORT_BY_NAME*>(base+names->u1.AddressOfData);
            if(strcmp(reinterpret_cast<char*>(name->Name),"XInputGetState"))continue;
            if(result)throw std::runtime_error("Ambiguous XInput import");result=reinterpret_cast<void**>(&slots->u1.Function);
        }
    }
    if(!result)throw std::runtime_error("XInputGetState import not found");return result;
}
}

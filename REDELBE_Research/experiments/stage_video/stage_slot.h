#pragma once
#include <string>
#include <string_view>
namespace stageinfo {
// Stage preview IDs use the numeric prefix of the canonical stage resource name.
// Alternative material/lighting resources (COL/LBN) are not selectable slots.
inline std::string slot(std::string_view texture) {
    if(texture=="stage_random"||texture=="stage_00_0")return "Random";
    constexpr std::string_view prefix="stage_";
    if(texture.substr(0,prefix.size())!=prefix)return {};
    texture.remove_prefix(prefix.size());
    if(texture.size()<4||texture[2]!='_')return "Unknown";
    unsigned first=0,second=0;
    for(unsigned i=0;i<2;++i){if(texture[i]<'0'||texture[i]>'9')return "Unknown";first=first*10+texture[i]-'0';}
    auto tail=texture.substr(3);
    if(tail.empty()||tail.size()>2)return "Unknown";
    for(char c:tail){if(c<'0'||c>'9')return "Unknown";second=second*10+c-'0';}
    static const char* codes[]={"S0101PIR","S0102PIR","S0201BST","S0301CRM","S0302CRM","S0401CLS","S0501PAS","S0502PAS","S0601LAB","S0701MUS","S0702MUS","S0801LOS","S0802LOS","S0901WAY","S1001KYO","S1101BAM","S1102BAM","S1201PRO","S1301GYM","S1501GRD","S1601ISL","S5001IOR","S5101SHP"};
    for(auto code:codes)if(unsigned((code[1]-'0')*10+code[2]-'0')==first&&unsigned((code[3]-'0')*10+code[4]-'0')==second)return code;
    return "Unknown";
}
inline std::string caption(std::string_view texture) {
    auto code=slot(texture);
    if(code.empty())return {};
    if(code=="Random")return "Slot: Random Vanilla Stage/Modded Stage";
    if(code=="Unknown")return "Slot: Random Vanilla Stage/Modded Stage";
    return "Slot: "+code+" Mod: Vanilla";
}
}

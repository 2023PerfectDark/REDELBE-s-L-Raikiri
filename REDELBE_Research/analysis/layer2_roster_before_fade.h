#pragma once
#include <cstdint>
#include <cstring>

// Native menu events, not raw controller polling: confirming Accessories may
// either hand focus to another character or finish selection altogether.
struct Layer2Roster {
    static constexpr uint32_t portraits=0xf403bcba;
    bool hidden=false;
    bool animation(uint32_t layout,const char* name) {
        if(!name)return false;
        bool before=hidden;
        if(layout==0xdd6728d2&&!strcmp(name,"detail_in"))hidden=true;
        if(layout==portraits&&(!strcmp(name,"icon_in")||
           !strcmp(name,"icon_on_p1")||!strcmp(name,"icon_on_p2")))hidden=false;
        if(layout==0xb384f573&&(!strcmp(name,"cos_in_p1")||
           !strcmp(name,"cos_in_p2")))hidden=false;
        // detail_out alone must not reveal a completed roster. The next
        // character/costume focus event restores it when selection continues.
        return hidden!=before;
    }
};

#pragma once
#include <cstdint>

// Let the game process its native body-release request before asking for the
// same resource ID again. All game calls stay on the initiating input thread.
struct Layer2PreviewReload {
    bool pending=false;
    uint64_t due=0;
    uint32_t thread=0;
    void begin(uint64_t now,uint32_t owner){pending=true;due=now+300;thread=owner;}
    void cancel(){pending=false;}
    bool take(uint64_t now,uint32_t owner,bool immediately=false){
        if(!pending||owner!=thread||(!immediately&&now<due))return false;
        pending=false;return true;
    }
};

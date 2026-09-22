#pragma once
#include <cstdint>

// The clock starts when both replacement parts are ready, not at the keypress.
struct Layer2CrossfadeClock {
    uint64_t requested=0, started=0;
    bool running=false, ready=false;
    void begin(uint64_t now){requested=now;started=0;running=true;ready=false;}
    void loaded(uint64_t now){if(running&&!ready){started=now;ready=true;}}
    float incoming(uint64_t now,unsigned duration) const {
        if(!running)return 1.0f;
        if(!ready)return 0.0f;
        float t=now<=started?0.0f:float(now-started)/float(duration?duration:1);
        if(t>=1.0f)return 1.0f;
        return t*t*(3.0f-2.0f*t);
    }
    bool expired(uint64_t now,unsigned duration) const {
        return running&&((ready&&now>=started&&now-started>=duration)||
                         (!ready&&now>=requested&&now-requested>=5000));
    }
    void cancel(){running=false;ready=false;}
};

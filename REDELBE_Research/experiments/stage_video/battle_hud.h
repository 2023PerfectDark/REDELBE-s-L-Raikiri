#pragma once
#include <cstdint>
#include <map>
// Exact HUD layout set recovered from original REDELBE; names verified in LR's name database.
static constexpr uint32_t battleHudLayouts[]={
 0x68c58d27,0x44774b37,0xa3476d26,0x54861cba,0xb6873be6,0x5adeac41,
 0xfd532010,0xd332b554,0x2b107044,0x4cfc5638,0xd7c47612,0x1b0565f4,
 0x950e531c,0x32503255,0xc0451ada,0x899e7208,0xe3ec1bc9,0x067e8cce,
 0xaaf4fcbf,0x134067c6,0x2f6cdd26,0xb0fb3d01};
struct BattleHudState {
 bool hidden=false,previousF5=false;
 uintptr_t owner=0;
 std::map<uint32_t,bool> requested;
 static bool contains(uint32_t hash){for(auto h:battleHudLayouts)if(h==hash)return true;return false;}
 void bind(uintptr_t next){if(next&&owner!=next){owner=next;requested.clear();}}
 bool show(uint32_t hash){if(!contains(hash))return true;requested[hash]=true;return !hidden;}
 void hide(uint32_t hash){if(contains(hash))requested[hash]=false;}
 bool restore(uint32_t hash)const{auto i=requested.find(hash);return i==requested.end()||i->second;}
 bool input(bool down,bool enabled){bool edge=down&&!previousF5;previousF5=down;if(!enabled||!edge)return false;hidden=!hidden;return true;}
};

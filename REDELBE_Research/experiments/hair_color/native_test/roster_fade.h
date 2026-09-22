#pragma once
#include <cstdint>
#include <map>
struct RosterFadeHover {
 uintptr_t focused=0;
 std::map<uintptr_t,uint64_t> departed;
 void begin(uintptr_t layout){focused=layout;departed.clear();}
 void enter(uintptr_t layout,uint64_t elapsed){
  if(!layout||focused==layout)return;
  if(focused)departed[focused]=elapsed;
  focused=layout;departed.erase(layout);
 }
 void leave(uintptr_t layout,uint64_t elapsed){if(layout&&focused==layout){departed[layout]=elapsed;focused=0;}}
 static float ramp(uint64_t elapsed,uint64_t duration){
  if(!duration||elapsed>=duration)return 1.f;
  float t=static_cast<float>(elapsed)/static_cast<float>(duration);return t*t*(3.f-2.f*t);
 }
 float alpha(uintptr_t layout,uint64_t elapsed,uint64_t duration)const{
  if(elapsed>=duration)return 1.f;
  if(layout&&layout==focused)return 1.f;
  auto it=departed.find(layout);
  if(it==departed.end())return ramp(elapsed,duration);
  if(elapsed<=it->second)return 0.f;
  return ramp(elapsed-it->second,duration-it->second);
 }
};

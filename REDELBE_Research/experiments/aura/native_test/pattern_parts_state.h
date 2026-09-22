#pragma once
#include <cstdint>
#include <atomic>
namespace patternparts {
struct ResultState {
 uint32_t p1=0,p2=0,w1=0,w2=0;unsigned status=0,lastResult=0,requested=0,added=0;
 bool wasZero=false;
 void observe(bool versus,uint32_t a,uint32_t b,uint32_t x,uint32_t y){
  if(!versus||!a||!b){status=0;p1=p2=0;wasZero=false;return;}
  bool zero=x==0&&y==0;
  if(a!=p1||b!=p2||(zero&&!wasZero)){p1=a;p2=b;w1=x;w2=y;status=1;lastResult=requested=added=0;}
  wasZero=zero;
 }
 unsigned consume(uint32_t x,uint32_t y){
  if(!status)return 0;
  if(x<w1||y<w2||(x>w1&&y!=w2)){w1=x;w2=y;status=1;lastResult=0;return 0;}
  unsigned outcome=x>w1?1:y>w2?2:0;
  if(outcome){w1=x;w2=y;lastResult=outcome;status=2;}return outcome;
 }
};
static ResultState result;
static std::atomic<bool> ready{false};
static uintptr_t settingsCell=0,queueCell=0;
static std::recursive_mutex lock;
static ULONGLONG observedAt=0;
struct Snapshot {uint32_t p1,p2,mode,config,w1,w2;};
template<class T> static bool read(uintptr_t p,T& value){SIZE_T got=0;return p&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&value,sizeof(value),&got)&&got==sizeof(value);}
static bool snapshot(Snapshot& s){
 uintptr_t root=0,first=0,last=0;
 if(!read(settingsCell,root)||!read(root+0x140,first)||!read(root+0x148,last)||!first||last<first||(last-first)%32||last-first>0x100000)return false;
 auto get=[&](uint32_t category,uint32_t field,unsigned index,uint32_t& out){
  size_t lo=0,hi=(last-first)/32;
  while(lo<hi){size_t mid=(lo+hi)/2;uint32_t pair[2]{};if(!read(first+mid*32,pair))return false;
   if(pair[0]<category||(pair[0]==category&&pair[1]<field))lo=mid+1;else hi=mid;}
  uintptr_t at=first+lo*32;uint32_t pair[2]{};uintptr_t begin=0,end=0;
  return at<last&&read(at,pair)&&pair[0]==category&&pair[1]==field&&read(at+8,begin)&&read(at+16,end)&&begin&&end>=begin&&end-begin<=1024&&end-begin>=(index+1)*4&&read(begin+index*4,out);
 };
 bool ok=get(0x2272be89,0x33335864,0,s.p1)&&get(0x2272be89,0x33335864,1,s.p2)&&get(0x2272be89,0x695cb57b,0,s.mode)&&get(0x2272be89,0x52c167f6,0,s.config)&&get(0xf06f4f3c,0x7eca3f54,0,s.w1)&&get(0xf06f4f3c,0x7eca3f54,1,s.w2);
 uintptr_t checkFirst=0,checkLast=0;return ok&&read(root+0x140,checkFirst)&&read(root+0x148,checkLast)&&first==checkFirst&&last==checkLast;
}
static bool versus(const Snapshot& s){return s.mode==0x19624807&&s.config==0x2bd6ff9a;}
static void observe(){
 if(!ready)return;std::lock_guard<std::recursive_mutex> guard(lock);
 auto now=GetTickCount64();if(now-observedAt<100)return;observedAt=now;
 Snapshot s{};if(snapshot(s))result.observe(versus(s),s.p1,s.p2,s.w1,s.w2);
}
}

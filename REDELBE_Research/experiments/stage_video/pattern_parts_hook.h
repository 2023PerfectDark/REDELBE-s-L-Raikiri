#pragma once
#include <random>
#include "pattern_parts_patterns.h"
namespace patternparts {
using CheckFn=uintptr_t(*)(void*);
using EmptyFn=bool(*)();
using PushFn=void(*)(uint32_t,uint32_t);
static CheckFn originalCheck=nullptr;
static EmptyFn originalEmpty=nullptr;
static PushFn push=nullptr;
static std::mt19937 random;
static bool stats(unsigned& count,unsigned& sum){
 uintptr_t root=0,first=0,last=0;count=sum=0;
 if(!read(queueCell,root)||!root||!read(root+0xb0,first)||!read(root+0xb8,last)||last<first||(last-first)%0x48||(last-first)/0x48>256)return false;
 for(auto p=first;p<last;p+=0x48){uint16_t quantity=0;if(!read(p+0x14,quantity))return false;++count;sum+=quantity;}return true;
}
static bool maybe(){
 std::lock_guard<std::recursive_mutex> guard(lock);
 if(!ready)return false;Snapshot s{};if(!snapshot(s))return false;
 result.observe(versus(s),s.p1,s.p2,s.w1,s.w2);
 if(!versus(s)||!result.status)return false;
 auto outcome=result.consume(s.w1,s.w2);
 if(outcome){
  unsigned amount=outcome==1&&userconfig::current.text("VersusPatternParts","win_reward_mode")=="custom"?
   static_cast<unsigned>(userconfig::current.number("VersusPatternParts","custom_win_amount")):
   std::uniform_int_distribution<unsigned>(1,outcome==1?100:10)(random);
  unsigned beforeCount=0,before=0,afterCount=0,after=0;
  if(amount<1||amount>100||!stats(beforeCount,before)){result.status=5;return false;}
  result.requested=amount;result.added=0; // Score change already consumed before the native call.
  push(s.p1,amount);
  if(!stats(afterCount,after)||after<before){result.status=5;return false;}
  result.added=after-before;if(!result.added)result.status=3;
  log("PATTERN PARTS P1 "+std::string(outcome==1?"win":"loss")+" requested="+std::to_string(amount)+" queued="+std::to_string(result.added));
 }
 unsigned count=0,sum=0;return result.status==2&&stats(count,sum)&&count>0;
}
static uintptr_t checkHook(void* object){maybe();return originalCheck(object);}
static bool emptyHook(){if(maybe())return false;return originalEmpty();}
static BYTE* rip(BYTE* instruction){int32_t offset=0;memcpy(&offset,instruction+3,4);return instruction+7+offset;}
static void install(){
 if(!userconfig::current.flag("VersusPatternParts","enabled")){log("PATTERN PARTS disabled by INI");return;}
 auto base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
 auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
 auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
 if(!dir.Size||dir.Size%sizeof(RUNTIME_FUNCTION)||uint64_t(dir.VirtualAddress)+dir.Size>nt->OptionalHeader.SizeOfImage)throw std::runtime_error("Parts function table invalid");
 auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);std::map<std::string,BYTE*> found;
 for(const auto& pattern:partsPatterns){
  std::vector<BYTE*> hits;
  for(size_t i=0;i<dir.Size/sizeof(*fs);++i){auto f=fs[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress<f.BeginAddress||f.EndAddress-f.BeginAddress!=pattern.size)continue;
   auto at=base+f.BeginAddress;bool match=true;for(size_t j=0;j<pattern.size;++j)if(pattern.mask[j]&&at[j]!=static_cast<BYTE>(pattern.bytes[j])){match=false;break;}
   if(!match)continue;
   if(!strcmp(pattern.name,"lr33Push")){auto tail=at+pattern.size-5;int32_t rel=0;memcpy(&rel,tail+1,4);if(*tail!=0xe9||tail+5+rel!=found["allocator"])continue;}
   hits.push_back(at);
  }
  if(!strcmp(pattern.name,"lr33GetSetting")){
   if(hits.empty()||hits.size()>2)throw std::runtime_error("Parts settings pattern not recognized");
   auto cell=rip(hits[0]+0x27);for(auto h:hits)if(rip(h+0x27)!=cell)throw std::runtime_error("Parts settings roots disagree");settingsCell=reinterpret_cast<uintptr_t>(cell);
  }else if(hits.size()!=1)throw std::runtime_error(std::string("Parts pattern missing/ambiguous: ")+pattern.name);
  found[pattern.name]=hits[0];
 }
 auto check=found["lr33Check"],empty=found["lr33Empty"],nativePush=found["lr33Push"];
 auto cell=rip(check+0x15);
 if(cell!=rip(empty+0x10)||cell!=rip(nativePush+0x1a))throw std::runtime_error("Parts reward roots disagree");
 queueCell=reinterpret_cast<uintptr_t>(cell);
 auto inImage=[&](uintptr_t p){return p>=reinterpret_cast<uintptr_t>(base)&&p+8<=reinterpret_cast<uintptr_t>(base)+nt->OptionalHeader.SizeOfImage;};
 if(!inImage(queueCell)||!inImage(settingsCell))throw std::runtime_error("Parts data pointer outside game");
 push=reinterpret_cast<PushFn>(nativePush);
 struct Prepared{BYTE* site;BYTE* relay;std::vector<BYTE> backup,patch;};std::vector<Prepared> patches;
 for(unsigned n=0;n<2;++n){
  auto site=n?empty:check;size_t length=n?11:6;auto relay=l2::allocateNear(site);
  l2::absoluteJump(relay,n?reinterpret_cast<void*>(emptyHook):reinterpret_cast<void*>(checkHook));
  auto trampoline=relay+128;memcpy(trampoline,site,length);
  if(n){auto destination=rip(site+4);int32_t delta=static_cast<int32_t>(destination-(trampoline+11));memcpy(trampoline+7,&delta,4);}
  l2::absoluteJump(trampoline+length,site+length);
  if(n)originalEmpty=reinterpret_cast<EmptyFn>(trampoline);else originalCheck=reinterpret_cast<CheckFn>(trampoline);
  DWORD old;if(!VirtualProtect(relay,0x1000,PAGE_EXECUTE_READ,&old))throw std::runtime_error("Parts relay protection failed");FlushInstructionCache(GetCurrentProcess(),relay,0x1000);
  std::vector<BYTE> patch(length,0x90);patch[0]=0xe9;int32_t delta=static_cast<int32_t>(relay-(site+5));memcpy(patch.data()+1,&delta,4);
  patches.push_back({site,relay,std::vector<BYTE>(site,site+length),patch});
 }
 unsigned seed=static_cast<unsigned>(GetTickCount64());BCryptGenRandom(nullptr,reinterpret_cast<PUCHAR>(&seed),sizeof(seed),BCRYPT_USE_SYSTEM_PREFERRED_RNG);random.seed(seed);
 unsigned applied=0;
 try{for(auto& p:patches){l2::write(p.site,p.patch.data(),p.patch.size());++applied;}}
 catch(...){for(unsigned i=0;i<applied;++i)l2::write(patches[i].site,patches[i].backup.data(),patches[i].backup.size());throw;}
 ready=true;log("PATTERN PARTS ready; win_mode="+userconfig::current.text("VersusPatternParts","win_reward_mode")+" custom="+userconfig::current.text("VersusPatternParts","custom_win_amount"));
}
}

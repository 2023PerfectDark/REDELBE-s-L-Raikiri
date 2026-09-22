#pragma once
#include "aura_descriptors.h"
#include "aura_expected.h"
#include "aura_sound.h"
namespace auratest {
struct Ref {void* object;void* control;};
using Start=void(*)(BYTE*);using Create=Ref*(*)(Ref*,const void*,void*);using Grow=void(*)(void*,void*,const Ref*);
static Start original=nullptr;static Create create=nullptr;static Grow grow=nullptr;static BYTE* image=nullptr;
static void releaseWeak(Ref& ref){if(ref.control&&InterlockedDecrement(reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(ref.control)+12))==0){auto vt=*reinterpret_cast<void***>(ref.control);reinterpret_cast<void(*)(void*)>(vt[1])(ref.control);}ref={};}
static int fighterSide(BYTE* fighter){
 auto map=*reinterpret_cast<BYTE**>(image+0x5ea7be8);if(!map)return -1;
 auto head=*reinterpret_cast<BYTE**>(map);if(!head)return -1;
 for(unsigned side=0;side<2;++side){
  auto node=*reinterpret_cast<BYTE**>(head+8);auto found=head;
  for(unsigned n=0;n<64&&node&&node!=head&&!node[25];++n){if(node[32]>=side){found=node;node=*reinterpret_cast<BYTE**>(node);}else node=*reinterpret_cast<BYTE**>(node+16);}
  if(found!=head&&found[32]==side&&*reinterpret_cast<BYTE**>(found+40)==fighter)return static_cast<int>(side);
 }
 return -1;
}
static int auraOption(const std::wstring& file){
 wchar_t value[32]{};GetPrivateProfileStringW(L"Aura",L"enabled",L"",value,32,file.c_str());
 if(!_wcsicmp(value,L"true")||!wcscmp(value,L"1"))return 1;
 if(!_wcsicmp(value,L"false")||!wcscmp(value,L"0"))return 0;
 return -1;
}
static int modOption(const l2::Mod& mod){
 // A stable user-owned sidecar survives regeneration of Kashira packages.
 if(!mod.name.empty()&&mod.name!="."&&mod.name!=".."&&mod.name.find_first_of("/\\:*?\"<>|")==std::string::npos){
  int option=auraOption(gameRoot+L"REDELBE_LR\\Layer2\\"+wide(mod.name)+L"\\mod.ini");if(option>=0)return option;
 }
 return auraOption(mod.iniPath);
}
static bool enabledFor(unsigned side){
 int option=auraOption(gameRoot+L"REDELBE_LR\\REDELBE.ini");bool result=option==1;
 std::lock_guard<std::recursive_mutex> lock(l2::mutex);
 auto found=l2::slots.find(l2::activeCostumes[side]);auto choice=l2::selections.current(side,l2::activeCostumes[side]);
 if(found!=l2::slots.end()&&choice&&choice<=found->second.size()){option=modOption(l2::mods[found->second[choice-1]]);if(option>=0)result=option==1;}
 auto choices=l2::hairChoices(l2::activeHairs[side],l2::activeFaces[side]);choice=l2::hairSelections.current(side,l2::activeHairs[side],l2::activeFaces[side]);
 if(choice&&choice<=choices.size()){option=modOption(l2::mods[choices[choice-1]]);if(option>=0)result=option==1;}
 return result;
}
static void snapshot(const char* label,void* address,size_t count){
 if(!address)return;BYTE data[512]{};SIZE_T got=0;if(count>sizeof(data)||!ReadProcessMemory(GetCurrentProcess(),address,data,count,&got)||got!=count)return;
 const char* digits="0123456789abcdef";std::string bytes;bytes.reserve(count*2);for(size_t i=0;i<count;++i){bytes+=digits[data[i]>>4];bytes+=digits[data[i]&15];}
 log(std::string("AURA SNAP ")+label+" at="+std::to_string(reinterpret_cast<uintptr_t>(address))+" bytes="+bytes);
}
// Capture dependencies synchronously while the factory still owns the objects.
// Only ReadProcessMemory is used; failed reads stop traversal.
template<class T> static bool peek(const void* address,T& value){SIZE_T got=0;return address&&ReadProcessMemory(GetCurrentProcess(),address,&value,sizeof(value),&got)&&got==sizeof(value);}
static void dependencySnapshot(BYTE* resource){
 BYTE* definition=nullptr;BYTE* node=nullptr;
 if(!resource)return;
 if(peek(resource+0x20,definition)&&definition){
  for(unsigned offset:{0x80u,0x88u}){BYTE* dependency=nullptr;if(peek(definition+offset,dependency)&&dependency){snapshot(offset==0x80?"dependency80":"dependency88",dependency,128);BYTE* data=nullptr;if(peek(dependency+0x20,data))snapshot("dependency_runtime",data,128);}}
 }
 if(!peek(resource+8,node))return;
 for(unsigned n=0;n<8&&node;++n){BYTE* raw=nullptr;BYTE* next=nullptr;if(!peek(node,raw)||!peek(node+8,next))break;snapshot("raw_node",node,16);if(reinterpret_cast<uintptr_t>(raw)>1)snapshot("raw_dependency",raw,64);if(next==node)break;node=next;}
}
// Pending controllers own the resource graph until native preparation completes.
// Retry only from the native effect update thread, never from a timer thread.
struct PendingAura {Ref ref{};ULONGLONG started=0,nextTry=0;bool sound=false;unsigned side=0;};
static PendingAura pending[30]{};
static std::recursive_mutex pendingMutex;
static std::atomic<unsigned> pendingCount{0};
static void releasePending(PendingAura& item){
 auto control=item.ref.control;item={};
 if(control){--pendingCount;reinterpret_cast<void(*)(void*)>(image+0x85d830)(control);}
}
static void clearPending(int side=-1){std::lock_guard<std::recursive_mutex> lock(pendingMutex);for(auto& item:pending)if(side<0||item.side==static_cast<unsigned>(side))releasePending(item);}
static bool holdPending(const Ref& ref,bool sound,unsigned side){
 auto count=reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(ref.control)+8);
 for(auto& item:pending)if(!item.ref.control){
  LONG n=InterlockedCompareExchange(count,0,0);
  while(n>0){LONG actual=InterlockedCompareExchange(count,n+1,n);if(actual==n){auto now=GetTickCount64();item={ref,now,now+50,sound,side};++pendingCount;return true;}n=actual;}
  break;
 }
 return false;
}
static bool updateEffect(BYTE* object,void* context,void* engine,float delta){
 if(pendingCount.load()){
  std::lock_guard<std::recursive_mutex> lock(pendingMutex);
  for(auto& item:pending)if(item.ref.object==object&&item.ref.control){
   auto now=GetTickCount64();
   if(now>=item.nextTry){
    item.nextTry=now+50;
    reinterpret_cast<void(*)(BYTE*)>(image+0x37f75d0)(object);
    if(object[0x4c]){
     if(item.sound)aurasound::track(item.ref.control,item.side);
     log("AURA READY instance="+l2::hex(*reinterpret_cast<uint32_t*>(object+0x44))+" wait_ms="+std::to_string(now-item.started));
     releasePending(item);
    }else if(now-item.started>=5000){
     log("AURA LOAD TIMEOUT instance="+l2::hex(*reinterpret_cast<uint32_t*>(object+0x44)));
     auto wrapper=*reinterpret_cast<BYTE**>(object+0x50);auto effect=wrapper?*reinterpret_cast<BYTE**>(wrapper+0x20):nullptr;
     if(effect)dependencySnapshot(*reinterpret_cast<BYTE**>(effect+0xa8));
     releasePending(item);
    }
   }
   break;
  }
 }
 return reinterpret_cast<bool(*)(BYTE*,void*,void*,float)>(image+0x37f7610)(object,context,engine,delta);
}
static void destroyManager(void* manager){clearPending();reinterpret_cast<void(*)(void*)>(image+0x37f6de0)(manager);}
static void startup(BYTE* fighter){
 original(fighter);
 if(!fighter)return;int side=fighterSide(fighter);if(side<0||!enabledFor(side))return;
 auto params=*reinterpret_cast<BYTE**>(fighter+0x78);if(!params)return;
 std::lock_guard<std::recursive_mutex> pendingLock(pendingMutex);
 auto vec=reinterpret_cast<Ref**>(fighter+0x170);
 // Preserve other native effects; only avoid duplicating an existing Raidou aura.
 for(auto entry=vec[0];entry&&entry!=vec[1];++entry){
  if(!entry->object||!entry->control||InterlockedCompareExchange(reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(entry->control)+8),0,0)<=0)continue;
  auto id=*reinterpret_cast<uint32_t*>(static_cast<BYTE*>(entry->object)+0x44);
  if(id==0x9db1990b||id==0x816ef40e||id==0x137d44fc){log("AURA skipped: native or custom aura already owned");return;}
 }
 clearPending(side);
 unsigned added=0;
 for(const auto& descriptor:auraDescriptors){
  Ref ref{};create(&ref,descriptor,fighter+0x130);
  if(added<3&&ref.object){auto obj=static_cast<BYTE*>(ref.object);auto wrapper=*reinterpret_cast<BYTE**>(obj+0x50);auto effect=wrapper?*reinterpret_cast<BYTE**>(wrapper+0x20):nullptr;log("AURA RESOURCE resolved="+l2::hex(*reinterpret_cast<uint32_t*>(obj+0x40))+" instance="+l2::hex(*reinterpret_cast<uint32_t*>(obj+0x44))+" wrapper="+std::to_string(reinterpret_cast<uintptr_t>(wrapper))+" effect="+std::to_string(reinterpret_cast<uintptr_t>(effect)));snapshot("controller",obj,128);snapshot("effect",effect,256);if(effect){snapshot("descriptor",*reinterpret_cast<void**>(effect+0xa0),512);auto resource=*reinterpret_cast<BYTE**>(effect+0xa8);snapshot("resource",resource,128);dependencySnapshot(resource);if(resource){snapshot("definition",*reinterpret_cast<void**>(resource+0x20),256);snapshot("resource_data",*reinterpret_cast<void**>(resource+0x40),256);}}}
  if(ref.object&&ref.control&&*reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(ref.control)+8)>0){
   if(vec[1]==vec[2])grow(vec,vec[1],&ref);
   else {InterlockedIncrement(reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(ref.control)+12));*vec[1]=ref;++vec[1];}
   auto controller=static_cast<BYTE*>(ref.object);
   if(controller[0x4c]){if(!added)aurasound::track(ref.control,side);}
   else if(!holdPending(ref,!added,side))log("AURA pending ownership unavailable");
   ++added;
  }
  releaseWeak(ref);
 }
 log("AURA TEST retained loading: player "+std::to_string(side+1)+" effects="+std::to_string(added));
}
static void install(const std::string& hash){
 if(GetPrivateProfileIntW(L"AuraResearch",L"native_test",0,(gameRoot+L"REDELBE_LR\\aura_test.ini").c_str())!=1)return;
 if(hash!="d1a9c6707575ce2cc932772124d9cf6ceba2f56ef060b8bd7b9d2e71828c4713")throw std::runtime_error("aura test executable differs");
 image=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
 for(const auto& expected:auraExpected)if(memcmp(image+expected.rva,expected.bytes,32))throw std::runtime_error("aura test code differs");
 if(memcmp(image+0x37f56b0,"\x48\x89\x4c\x24\x08\x57\x48\x83\xec\x40",10))throw std::runtime_error("aura preload wrapper differs");
 original=reinterpret_cast<Start>(image+0x3a5c610);create=reinterpret_cast<Create>(image+0x3998bc0);grow=reinterpret_cast<Grow>(image+0x2b68710);
 struct Hook {unsigned site,target;void* function;};
 const Hook resourceHooks[]={
 {0x24b52fa,0x37f7610,reinterpret_cast<void*>(&updateEffect)},
 {0x24b550c,0x37f7610,reinterpret_cast<void*>(&updateEffect)},
 {0x24b56cf,0x37f7610,reinterpret_cast<void*>(&updateEffect)},
 {0x24b57c5,0x37f7610,reinterpret_cast<void*>(&updateEffect)},
 {0x37f6cfd,0x37f7610,reinterpret_cast<void*>(&updateEffect)},
 {0x24b60dd,0x37f6de0,reinterpret_cast<void*>(&destroyManager)},
 {0x24b69f9,0x37f6de0,reinterpret_cast<void*>(&destroyManager)}};
 for(const auto& hook:resourceHooks){auto p=image+hook.site;int32_t offset;memcpy(&offset,p+1,4);if((*p!=0xe8&&*p!=0xe9)||p+5+offset!=image+hook.target)throw std::runtime_error("aura lifetime call differs");}
 const unsigned sites[]={0x2832505,0x28c3a57,0x28d34a7,0x398e02a};
 for(auto rva:sites){auto p=image+rva;int32_t d;memcpy(&d,p+1,4);if((*p!=0xe8&&*p!=0xe9)||p+5+d!=image+0x3a5c610)throw std::runtime_error("aura test call differs");}
 for(auto rva:sites){auto p=image+rva;auto relay=l2::allocateNear(p);l2::absoluteJump(relay,reinterpret_cast<void*>(&startup));DWORD old;VirtualProtect(relay,0x1000,PAGE_EXECUTE_READ,&old);FlushInstructionCache(GetCurrentProcess(),relay,0x1000);BYTE patch[5]={*p};int32_t d=static_cast<int32_t>(relay-(p+5));memcpy(patch+1,&d,4);l2::write(p,patch,5);}
 for(const auto& hook:resourceHooks){auto p=image+hook.site;auto relay=l2::allocateNear(p);l2::absoluteJump(relay,hook.function);DWORD old;VirtualProtect(relay,0x1000,PAGE_EXECUTE_READ,&old);FlushInstructionCache(GetCurrentProcess(),relay,0x1000);BYTE patch[5]={*p};int32_t offset=static_cast<int32_t>(relay-(p+5));memcpy(patch+1,&offset,4);l2::write(p,patch,5);}
 try {aurasound::install();}catch(const std::exception& e){log(std::string("AURA SOUND disabled: ")+e.what());}
 log("AURA TEST native startup installed; both players, INI policy, existing aura preserved");
}
}



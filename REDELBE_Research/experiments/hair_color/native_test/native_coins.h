#pragma once
#include <cstring>
#include <functional>
namespace nativecoins {
struct Addresses {BYTE* wallet=nullptr;BYTE* owner=nullptr;BYTE* save=nullptr;};
static bool resolve(BYTE* base,size_t size,Addresses& out){
 auto within=[&](BYTE* p,size_t n){return p>=base&&size_t(p-base)<=size&&n<=size-size_t(p-base);};
 auto rel=[&](BYTE* p,int displacement,int length)->BYTE*{if(!within(p,length))return nullptr;int32_t d;memcpy(&d,p+displacement,4);auto offset=int64_t(p-base)+length+d;if(offset<0||uint64_t(offset)>=size)return nullptr;return base+offset;};
 auto reference=[&](const char* label)->BYTE*{
  BYTE* result=nullptr;size_t length=strlen(label)+1;
  auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);if(!within(base+dos->e_lfanew,sizeof(IMAGE_NT_HEADERS64)))return nullptr;
  auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+dos->e_lfanew);auto sections=IMAGE_FIRST_SECTION(nt);
  for(unsigned s=0;s<nt->FileHeader.NumberOfSections;++s){if(!(sections[s].Characteristics&IMAGE_SCN_MEM_EXECUTE))continue;
   size_t first=sections[s].VirtualAddress,last=first+sections[s].Misc.VirtualSize;if(last>size)return nullptr;
   for(size_t i=first;i+7<=last;++i){auto p=base+i;if(memcmp(p,"\x48\x8d\x05",3))continue;auto text=rel(p,3,7);
    if(!text||!within(text,length)||text==base||text[-1]||memcmp(text,label,length))continue;
    if(result)return nullptr;result=p;
   }
  }return result;
 };
 auto money=reference("ingame_money"),registration=reference("scene::request_save_system_data");if(!money||!registration)return false;
 if(!within(money,30)||memcmp(money+23,"\x48\x8d\x05",3))return false;
 auto accessor=rel(money+23,3,7);if(!accessor||!within(accessor,26)||accessor[21]!=0xe8)return false;
 auto getter=rel(accessor+21,1,5);if(!getter||!within(getter,64)||memcmp(getter+53,"\x48\x8b\x05",3)||memcmp(getter+60,"\x48\x83\xc4\x38",4))return false;
 auto wallet=rel(getter+53,3,7);
 if(!within(registration,17)||registration[12]!=0xe8)return false;auto reg=rel(registration+12,1,5);
 if(!reg||!within(reg,55)||memcmp(reg+48,"\x48\x8d\x05",3))return false;auto handler=rel(reg+48,3,7);
 if(!handler||!within(handler,84)||memcmp(handler+70,"\x48\x8b\x0d",3)||handler[77]!=0xe8||memcmp(handler+82,"\x33\xc0",2))return false;
 auto owner=rel(handler+70,3,7),save=rel(handler+77,1,5);
 if(!wallet||!owner||!save||!within(wallet,8)||!within(owner,8)||!within(save,8))return false;
 out={wallet,owner,save};return true;
}
static Addresses addresses;
static bool attempted=false,available=false;
static bool initialize(){
 if(attempted)return available;attempted=true;
 auto b=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(b+reinterpret_cast<IMAGE_DOS_HEADER*>(b)->e_lfanew);
 available=resolve(b,nt->OptionalHeader.SizeOfImage,addresses);log(available?"COINS native balance/save request resolved":"COINS native balance/save request unavailable; purchases disabled");return available;
}
static bool read(uint32_t*& coins,void*& owner){
 if(!initialize())return false;
 __try {coins=*reinterpret_cast<uint32_t**>(addresses.wallet);owner=*reinterpret_cast<void**>(addresses.owner);return coins&&owner&&*coins<=999999999;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
static uint32_t balance(){uint32_t* p=nullptr;void* owner=nullptr;return read(p,owner)?*p:0;}
static bool debit(uint32_t cost){
 uint32_t* p=nullptr;void* owner=nullptr;if(!read(p,owner)||*p<cost)return false;
 // Called on the wardrobe game thread. Match native purchases: decrement the
 // saved system-data field, then queue scene::request_save_system_data.
 *p-=cost;reinterpret_cast<void(*)(void*)>(addresses.save)(owner);
 log("COINS hair color charged="+std::to_string(cost)+" balance="+std::to_string(*p));return true;
}
}

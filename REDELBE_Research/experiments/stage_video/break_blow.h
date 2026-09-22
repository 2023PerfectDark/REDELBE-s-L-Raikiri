#pragma once
#include "break_blow_patterns.h"
namespace breakblow {
inline BYTE* resolve(BYTE* base) {
 auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);
 if(dos->e_magic!=IMAGE_DOS_SIGNATURE)throw std::runtime_error("invalid DOS header");
 auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+dos->e_lfanew);
 if(nt->Signature!=IMAGE_NT_SIGNATURE)throw std::runtime_error("invalid PE header");
 auto size=nt->OptionalHeader.SizeOfImage;
 auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
 if(!dir.Size||dir.Size%sizeof(RUNTIME_FUNCTION)||uint64_t(dir.VirtualAddress)+dir.Size>size)throw std::runtime_error("invalid function table");
 auto fs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);BYTE* hits[2]={};
 for(unsigned p=0;p<2;++p) {
  const auto& sig=breakBlowPatterns[p];
  for(unsigned i=0;i<dir.Size/sizeof(*fs);++i) {
   auto rva=fs[i].BeginAddress;
   if(uint64_t(rva)+sig.size>size||fs[i].EndAddress<=rva)continue;
   bool match=true;
   for(size_t j=0;j<sig.size;++j)if(sig.mask[j]&&base[rva+j]!=static_cast<BYTE>(sig.data[j])){match=false;break;}
   if(!match)continue;
   if(hits[p])throw std::runtime_error(std::string("ambiguous ")+sig.name);
   hits[p]=base+rva;
  }
  if(!hits[p])throw std::runtime_error(std::string("unrecognized ")+sig.name);
 }
 int32_t delta;memcpy(&delta,hits[0]+0x40,4);
 if(hits[0][0x3f]!=0xe8||hits[0]+0x44+delta!=hits[1])throw std::runtime_error("property call mismatch");
 if(hits[0][0x46]!=0x74||hits[0][0x47]!=0x4b||hits[0][0x93]!=0xb0||hits[0][0x94]!=1)throw std::runtime_error("branch destination mismatch");
 return hits[0]+0x46;
}
}

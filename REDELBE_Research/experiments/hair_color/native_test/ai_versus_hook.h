#pragma once
namespace aivsai {
static void install() {
 auto base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
 auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
 auto sig=l2::bytes("48 8B 00 48 8B 40 08 0F B6 14 B0 EB 02 33 D2 42 88 94 35 BE 00 00 00");
 BYTE* found=nullptr;auto section=IMAGE_FIRST_SECTION(nt);
 for(unsigned s=0;s<nt->FileHeader.NumberOfSections;++s){
  if(!(section[s].Characteristics&IMAGE_SCN_MEM_EXECUTE))continue;
  size_t begin=section[s].VirtualAddress,end=begin+section[s].Misc.VirtualSize;
  if(end>nt->OptionalHeader.SizeOfImage||end<begin)throw std::runtime_error("AI code section bounds invalid");
  for(size_t i=begin;i+sig.size()<=end;++i)if(base[i]==sig[0]&&!memcmp(base+i,sig.data(),sig.size())){
   if(found)throw std::runtime_error("AI CPU pattern ambiguous");found=base+i;
  }
 }
 if(!found)throw std::runtime_error("AI CPU pattern not recognized");
 auto site=found+15;auto relay=l2::allocateNear(site);
 // Preserve RAX and flags; DL changes only for fighter slots 0 and 1 while armed.
 auto code=l2::bytes("50 9C 48 B8 00 00 00 00 00 00 00 00 80 38 00 74 07 83 FE 01 77 02 B2 01 9D 58 42 88 94 35 BE 00 00 00");
 auto flag=reinterpret_cast<uintptr_t>(&cpuBoth);memcpy(code.data()+4,&flag,8);
 // Capture the native CPU flags (including the AI-vs-AI override), preserving
 // the original RAX and flags. A new P1 snapshot starts a color-roll epoch.
 code.resize(code.size()-10);
 auto capture=l2::bytes("83 FE 01 77 0D 48 B8 00 00 00 00 00 00 00 00 88 14 30 85 F6 75 0C 48 B8 00 00 00 00 00 00 00 00 FF 00 9D 58 42 88 94 35 BE 00 00 00");
 auto cpus=reinterpret_cast<uintptr_t>(&fighterCpu[0]);memcpy(capture.data()+7,&cpus,8);
 auto epoch=reinterpret_cast<uintptr_t>(&cpuGeneration);memcpy(capture.data()+24,&epoch,8);
 code.insert(code.end(),capture.begin(),capture.end());
 memcpy(relay,code.data(),code.size());l2::absoluteJump(relay+code.size(),site+8);
 DWORD old;if(!VirtualProtect(relay,0x1000,PAGE_EXECUTE_READ,&old))throw std::runtime_error("AI relay protection failed");
 FlushInstructionCache(GetCurrentProcess(),relay,0x1000);
 BYTE patch[8]={0xe9,0,0,0,0,0x90,0x90,0x90};auto distance=relay-(site+5);
 if(distance<INT32_MIN||distance>INT32_MAX)throw std::runtime_error("AI relay out of range");
 int32_t jump=static_cast<int32_t>(distance);memcpy(patch+1,&jump,4);
 l2::write(site,patch,8);available=true;
 log("AI VS AI CPU hook ready RVA="+std::to_string(site-base));
}
}

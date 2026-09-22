#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <map>
#include <string>
#include <vector>
#include <algorithm>
#include <fstream>
#include <iterator>
#include <iostream>
#include "game_patterns.h"
int main(int argc,char** argv) {
 try {
  for(int i=1;i<argc;++i) {
   std::ifstream in(argv[i],std::ios::binary);std::vector<BYTE> b((std::istreambuf_iterator<char>(in)),{});
   if(b.empty())throw std::runtime_error("Missing image");
   gamecode::resolve(b.data());gamecode::xinputCell(b.data());
   for(const auto& p:gamecode::resolved)std::cout<<p.first<<" "<<std::hex<<(p.second-b.data())<<"\n";
   auto where=gamecode::get("defaults")-b.data();b[where]^=1;bool rejected=false;
   try{gamecode::resolve(b.data());}catch(const std::exception&){rejected=true;}
   if(!rejected)throw std::runtime_error("Changed code accepted");b[where]^=1;
   auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(b.data()+reinterpret_cast<IMAGE_DOS_HEADER*>(b.data())->e_lfanew);
   auto d=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];auto f=reinterpret_cast<RUNTIME_FUNCTION*>(b.data()+d.VirtualAddress);
   auto saved=f[d.Size/sizeof(*f)-1];
   for(unsigned j=0;j<d.Size/sizeof(*f);++j)if(f[j].BeginAddress==where){f[d.Size/sizeof(*f)-1]=f[j];break;}
   rejected=false;try{gamecode::resolve(b.data());}catch(const std::exception&){rejected=true;}
   if(!rejected)throw std::runtime_error("Ambiguous code accepted");f[d.Size/sizeof(*f)-1]=saved;
   std::cout<<"PASS: "<<argv[i]<<" resolves uniquely; modified and ambiguous code rejected\n";
  }
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}

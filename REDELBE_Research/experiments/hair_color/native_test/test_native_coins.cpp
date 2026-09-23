#include <windows.h>
#include <string>
#include <fstream>
#include <vector>
#include <iostream>
static void log(const std::string&){}
#include "native_coins.h"
int main(int argc,char** argv){
 if(argc!=2)return 1;std::ifstream f(argv[1],std::ios::binary);std::vector<BYTE> b((std::istreambuf_iterator<char>(f)),{});nativecoins::Addresses a;
 if(b.empty()||!nativecoins::resolve(b.data(),b.size(),a))return 2;
 std::cout<<std::hex<<(a.wallet-b.data())<<" "<<(a.owner-b.data())<<" "<<(a.save-b.data())<<"\n";
 return (a.save-b.data())==0x227f430?0:3;
}

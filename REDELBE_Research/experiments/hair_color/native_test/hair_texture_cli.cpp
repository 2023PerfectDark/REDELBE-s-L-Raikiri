#include "hair_texture.h"
#include <fstream>
#include <iostream>
#include <iterator>
#include <filesystem>
#include <string>
int main(int argc,char** argv){try{
    if(argc!=4){std::cerr<<"hair_texture INPUT.g1t NEW_OUTPUT.g1t RRGGBB|decode\n";return 2;}
    if(std::filesystem::exists(argv[2]))throw std::runtime_error("Output already exists");
    std::ifstream in(argv[1],std::ios::binary);if(!in)throw std::runtime_error("Cannot read input");
    hairtexture::Bytes src((std::istreambuf_iterator<char>(in)),{});
    bool decode=std::string(argv[3])=="decode";size_t parsed=0;auto color=decode?0:std::stoul(argv[3],&parsed,16);
    if(!decode&&(parsed!=6||color>0xffffff))throw std::runtime_error("Color must be six hexadecimal digits");
    auto result=hairtexture::convert(src,uint32_t(color),!decode);
    std::ofstream out(argv[2],std::ios::binary);out.write(reinterpret_cast<const char*>(result.data()),result.size());if(!out)throw std::runtime_error("Cannot write output");
    std::cout<<"Wrote "<<result.size()<<" bytes\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}

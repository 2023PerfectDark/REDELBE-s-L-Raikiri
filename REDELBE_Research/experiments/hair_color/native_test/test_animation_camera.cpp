#define NOMINMAX
#include <windows.h>
#include <xinput.h>
#include <vector>
#include <memory>
#include <atomic>
#include <mutex>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <iostream>
namespace animationpreviewtest {
struct Clip{float seconds;};static std::shared_ptr<Clip> selected;
static std::atomic<bool> expanded{},active{},paused{};
static std::atomic<ULONGLONG> wardrobeUntil{},appliedAt{},started{};
static std::atomic<float> position{};
template<class T>static T at(const unsigned char* p,size_t n){T x;memcpy(&x,p+n,sizeof x);return x;}
template<class T>static void put(unsigned char* p,size_t n,T x){memcpy(p+n,&x,sizeof x);}
static bool read(const void* p,void* out,size_t n){SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;}
static void log(const std::string&){}
#include "animation_camera.h"
}
int wmain(int argc,wchar_t** argv){
 auto fight=animationpreviewtest::camera::fightingView();
 // Neutral camera must frame the full upright character at the origin.
 float halfHeight=tanf(fight.fov*.5f)*fight.p[2];
 if(!animationpreviewtest::camera::valid(fight)||fight.p[1]-halfHeight>0||fight.p[1]+halfHeight<200)return 1;
 auto orbited=fight;animationpreviewtest::camera::orbit(orbited,1.57079632679f,0);
 if(fabs(orbited.p[0]-400)> .01f||fabs(orbited.p[2])>.01f)return 1;
 animationpreviewtest::camera::orbit(orbited,-1.57079632679f,.4f);
 float radius=sqrtf(orbited.p[0]*orbited.p[0]+powf(orbited.p[1]-92.5f,2)+orbited.p[2]*orbited.p[2]);
 if(fabs(radius-400)>.01f||!animationpreviewtest::camera::valid(orbited))return 1;
 if(argc!=2)return 2;unsigned passed=0,rejected=0;std::vector<unsigned char> valid;
 for(auto& entry:std::filesystem::directory_iterator(argv[1]))if(entry.path().extension()==L".g1a"){
  auto file=animationpreviewtest::camera::load(entry.path().wstring());if(file){++passed;if(valid.empty())valid=file->bytes;}else{++rejected;std::cout<<"Rejected "<<entry.path().filename().string()<<"\n";}
 }
 std::cout<<"Validated "<<passed<<"; rejected "<<rejected<<"\n";
 if(valid.empty())return 1;
 auto temp=std::filesystem::temp_directory_path()/(L"redelbe_camera_validation_"+std::to_wstring(GetCurrentProcessId())+L".g1a");
 for(int test=0;test<5;++test){auto corrupt=valid;
  if(test==0)corrupt.resize(corrupt.size()-1);
  if(test==1)memset(corrupt.data()+32,255,4);
  if(test==2)animationpreviewtest::put<uint32_t>(corrupt.data(),16,0x7fc00000);
  size_t table=(size_t(animationpreviewtest::at<uint32_t>(valid.data(),32))+2)*16;
  if(test==3)animationpreviewtest::put<uint32_t>(corrupt.data(),table+8,0x7fffffff);
  if(test==4){auto track=table+size_t(animationpreviewtest::at<uint32_t>(valid.data(),table+8))*16;animationpreviewtest::put<uint32_t>(corrupt.data(),track+4,0);}
  {std::ofstream f(temp,std::ios::binary);f.write((char*)corrupt.data(),corrupt.size());}
  if(animationpreviewtest::camera::load(temp.wstring())){std::filesystem::remove(temp);std::cerr<<"Unsafe file accepted\n";return 1;}
 }
 std::filesystem::remove(temp);std::cout<<"Five malformed camera files rejected\n";
 return rejected?1:0;
}

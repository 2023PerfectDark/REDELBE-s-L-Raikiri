#pragma once
#include <cmath>
#include <memory>
#pragma comment(lib,"gdi32.lib")
// Local proof of native motion playback. Not a public browser or camera player.
// Owned data stays alive for the DLL lifetime; game-owned resource handles are
// never retained or modified. Only an explicitly armed Wardrobe test can run.
namespace animationpreviewtest {
struct Clip {std::vector<unsigned char> file,payload;float seconds=0;uint16_t bones=0;};
static std::shared_ptr<Clip> selected;
static std::shared_ptr<Clip> selectedFace;
static std::atomic<bool> expanded{},paused{};
static std::atomic<float> position{};
static std::atomic<ULONGLONG> appliedAt{};
static std::atomic<ULONGLONG> wardrobeUntil{};
static std::atomic<bool> active{};
static std::atomic<bool> enabled{};
static std::atomic<ULONGLONG> started{};

template<class T> static T at(const unsigned char* p,size_t offset){T v{};memcpy(&v,p+offset,sizeof(v));return v;}
template<class T> static void put(unsigned char* p,size_t offset,T v){memcpy(p+offset,&v,sizeof(v));}
static bool read(const void* p,void* out,size_t n){SIZE_T got=0;return p&&ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;}
static bool loadClip(const std::wstring& path,bool facial=false){
 auto clip=std::make_shared<Clip>();auto& file=clip->file;auto& payload=clip->payload;auto& bones=clip->bones;auto& seconds=clip->seconds;
 std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)return false;
 auto size=in.tellg();if(size<32||size>16*1024*1024)return false;
 file.resize(static_cast<size_t>(size));in.seekg(0);if(!in.read(reinterpret_cast<char*>(file.data()),size)){file.clear();return false;}
 auto p=file.data();if(memcmp(p,"_A2G0400",8)||at<uint32_t>(p,8)!=file.size())return false;
 auto fps=at<float>(p,12);auto frames=at<uint16_t>(p,16);bones=at<uint16_t>(p,18)>>4;
 auto keySize=at<uint32_t>(p,20),vectors=at<uint32_t>(p,24);
 if(!std::isfinite(fps)||fps<=0||fps>240||!frames||!bones||bones>1024)return false;
 size_t key=32+size_t(bones)*4,packed=key+keySize;
 if(packed>file.size()||uint64_t(packed)+uint64_t(vectors)*32!=file.size())return false;
 // Validate each channel, key time and packed-vector range before native use.
 for(unsigned b=0;b<bones;++b){auto entry=at<uint32_t>(p,32+b*4);unsigned count=entry&15;size_t pos=key+size_t(entry>>16)*4;
  if(!count||count>3)return false;unsigned seen=0;
  for(unsigned c=0;c<count;++c){if(pos+8>packed)return false;auto op=at<uint16_t>(p,pos),n=at<uint16_t>(p,pos+2);auto first=at<uint32_t>(p,pos+4);
   if(op>2||(seen&(1u<<op))||!n||uint64_t(first)+n>vectors||pos+8+size_t(n)*2>packed)return false;seen|=1u<<op;
   unsigned previous=0;for(unsigned k=0;k<n;++k){auto t=at<uint16_t>(p,pos+8+k*2);if(t>frames||(k&&t<previous))return false;previous=t;}
   pos+=8+((size_t(n)*2+3)&~size_t(3));
  }
 }
 payload.resize(48+file.size()-32+31);memcpy(payload.data()+48,p+32,packed-32);
 auto packedData=reinterpret_cast<unsigned char*>((reinterpret_cast<uintptr_t>(payload.data()+48+packed-32)+31)&~uintptr_t(31));
 memcpy(packedData,p+packed,file.size()-packed);
 put(payload.data(),0,fps);put(payload.data(),4,frames);put(payload.data(),8,bones);put<uint32_t>(payload.data(),12,1);
 put(payload.data(),24,payload.data()+48);put(payload.data(),32,payload.data()+48+bones*4);put(payload.data(),40,packedData);
 seconds=frames/fps;
 if(facial){auto body=std::atomic_load(&selected);if(!body||std::fabs(body->seconds-seconds)>.05f||bones!=344)return false;std::atomic_store(&selectedFace,clip);return true;}
 std::atomic_store(&selectedFace,std::shared_ptr<Clip>{});std::atomic_store(&selected,clip);position=0;started=GetTickCount64();paused=false;appliedAt=0;return true;
}
// Direct facial evaluator receives a native resource, not the body wrapper.
static bool substituteFace(void* motion,unsigned char* native,float& time,std::shared_ptr<Clip>& keep){
 if(!active||GetTickCount64()>wardrobeUntil)return false;
 keep=std::atomic_load(&selectedFace);if(!keep||!read(motion,native,32))return false;
 unsigned char source[48]{};
 if(!(at<uint32_t>(native,20)&0x80000000)||!read(at<void*>(native,24),source,48)||at<uint16_t>(source,8)!=keep->bones)return false;
 uint32_t ids[1024]{};if(!read(at<void*>(source,24),ids,keep->bones*4))return false;
 for(unsigned i=0;i<keep->bones;++i)if((ids[i]&0x3ff0)!=(at<uint32_t>(keep->file.data(),32+i*4)&0x3ff0))return false;
 put(native,8,keep->seconds);put(native,24,keep->payload.data());
 time=paused?position.load():static_cast<float>(std::fmod(position.load()+(GetTickCount64()-started.load())/1000.0,keep->seconds));
 return true;
}
#include "animation_camera.h"
#include "animation_browser_ui.h"
static bool substitute(void* motion,unsigned char* native,float& time,std::shared_ptr<Clip>& keep){
 if(!active||GetTickCount64()>wardrobeUntil)return false;
 keep=std::atomic_load(&selected);if(!keep)return false;
 unsigned char wrapper[64]{};if(!read(motion,wrapper,sizeof(wrapper))||at<uint32_t>(wrapper,16)!=1)return false;
 uintptr_t handle=0,child=0;
 if(!read(at<void*>(wrapper,56),&handle,8)||!read(reinterpret_cast<void*>(handle+32),&child,8)||!read(reinterpret_cast<void*>(child),native,32))return false;
 unsigned char source[48]{};if(!(at<uint32_t>(native,20)&0x80000000)||!read(at<void*>(native,24),source,48))return false;
 if(at<uint16_t>(source,8)!=keep->bones){auto face=std::atomic_load(&selectedFace);if(!face||at<uint16_t>(source,8)!=face->bones)return false;keep=face;}
 auto& file=keep->file;auto& payload=keep->payload;auto bones=keep->bones;auto seconds=keep->seconds;
 // Same bone IDs only: face/hair/other skeleton animations cannot be substituted.
 uint32_t ids[1024]{};if(!read(at<void*>(source,24),ids,bones*4))return false;
 for(unsigned i=0;i<bones;++i)if((ids[i]&0x3ff0)!=(at<uint32_t>(file.data(),32+i*4)&0x3ff0))return false;
 put(native,8,seconds);put(native,24,payload.data());
 time=paused?position.load():static_cast<float>(std::fmod(position.load()+(GetTickCount64()-started.load())/1000.0,seconds));appliedAt=GetTickCount64();return true;
}
}

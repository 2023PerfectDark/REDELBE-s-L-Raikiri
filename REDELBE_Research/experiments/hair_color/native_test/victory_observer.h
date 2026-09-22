#pragma once
// Bounded read-only identification of native Kasumi victory playback.
namespace victoryobserver {
struct Reference {std::string name;std::vector<unsigned char> file;};
static std::vector<Reference> references;
static std::mutex lock;
static ULONGLONG last=0;
static unsigned samples=0;
static std::vector<std::pair<void*,unsigned>> candidates;
// Capture owned bytes while the evaluator still owns the source. A pointer
// logged here is not safe to dereference after the intro has finished.
static unsigned captureCount=0;
static size_t captureBytes=0;
static std::set<uint64_t> captureHashes;
static ULONGLONG captureChecked=0;
static void capture(const unsigned char* source,float time){
 using namespace animationpreviewtest;
 const unsigned bones=at<uint16_t>(source,8),frames=at<uint16_t>(source,4);
 const float fps=at<float>(source,0);
 if(bones!=57||!frames||frames>36000||!std::isfinite(fps)||fps<1||fps>240||captureCount>=32)return;
 auto now=GetTickCount64();if(now-captureChecked<250)return;captureChecked=now;
 std::vector<unsigned char> table(bones*4),keys;
 if(!read(at<void*>(source,24),table.data(),table.size()))return;
 size_t keySize=0,vectorCount=0;
 for(unsigned b=0;b<bones;++b){
  auto entry=at<uint32_t>(table.data(),b*4);unsigned channels=entry&15;
  size_t pos=size_t(entry>>16)*4;if(!channels||channels>3)return;
  for(unsigned c=0;c<channels;++c){
   unsigned char h[8]{};if(pos>1024*1024||!read(static_cast<unsigned char*>(at<void*>(source,32))+pos,h,8))return;
   unsigned op=at<uint16_t>(h,0),count=at<uint16_t>(h,2),first=at<uint32_t>(h,4);
   if(op>2||!count||uint64_t(first)+count>262144)return;
   pos+=8+((size_t(count)*2+3)&~size_t(3));
   keySize=std::max(keySize,pos);vectorCount=std::max(vectorCount,size_t(first)+count);
  }
 }
 const size_t size=32+table.size()+keySize+vectorCount*32;
 if(size>8*1024*1024||captureBytes+size>64*1024*1024)return;
 std::vector<unsigned char> file(size);auto p=file.data();
 memcpy(p,"_A2G0400",8);put<uint32_t>(p,8,static_cast<uint32_t>(size));put(p,12,fps);
 put<uint16_t>(p,16,static_cast<uint16_t>(frames));put<uint16_t>(p,18,static_cast<uint16_t>(bones<<4));
 put<uint32_t>(p,20,static_cast<uint32_t>(keySize));put<uint32_t>(p,24,static_cast<uint32_t>(vectorCount));
 memcpy(p+32,table.data(),table.size());
 if(!read(at<void*>(source,32),p+32+table.size(),keySize)||!read(at<void*>(source,40),p+32+table.size()+keySize,vectorCount*32))return;
 uint64_t hash=14695981039346656037ull;for(auto byte:file){hash^=byte;hash*=1099511628211ull;}
 if(!captureHashes.insert(hash).second)return;
 auto dir=gameRoot+L"REDELBE_LR\\NativeIntroCapture";CreateDirectoryW(dir.c_str(),nullptr);
 auto path=dir+L"\\body_"+std::to_wstring(hash)+L".g1a";
 std::ofstream out(path,std::ios::binary);if(!out.write(reinterpret_cast<const char*>(p),file.size()))return;
 ++captureCount;captureBytes+=size;
 std::ostringstream line;line<<"INTRO CAPTURE file="<<utf8(path)<<" frames="<<frames<<" fps="<<fps<<" time="<<time;log(line.str());
}
static void initialize(){
 if(GetFileAttributesW((gameRoot+L"REDELBE_LR\\victory_trace.enabled").c_str())==INVALID_FILE_ATTRIBUTES)return;
 for(const auto& pair:std::vector<std::pair<std::string,std::wstring>>{{"KAS07020_WIN",L"0xa768919b.g1a"},{"KAS07120_WIN",L"0x0143fbdc.g1a"},{"KAS07010_ENT",L"0x219ac50b.g1a"},{"KAS07110_ENT",L"0x7b762f4c.g1a"}}){
  std::ifstream in(gameRoot+L"REDELBE_LR\\AnimationBrowser\\Clips\\"+pair.second,std::ios::binary|std::ios::ate);
  if(!in)continue;auto size=in.tellg();if(size<32||size>16*1024*1024)continue;
  Reference r{pair.first,std::vector<unsigned char>(size_t(size))};in.seekg(0);
  if(in.read((char*)r.file.data(),size)&&!memcmp(r.file.data(),"_A2G0400",8))references.push_back(std::move(r));
 }
 log("VICTORY OBSERVER references="+std::to_string(references.size()));
}
static void observe(void* motion,void* skeleton,float time,bool direct=false){
 using namespace animationpreviewtest;
 if(references.empty()||expanded)return;
 std::unique_lock<std::mutex> guard(lock,std::try_to_lock);if(!guard.owns_lock()||samples>=120)return;
 auto now=GetTickCount64();if(now-last<1000)return;
 unsigned char wrapper[64]{},native[32]{},source[48]{};uintptr_t handle=0,child=0;
 if(direct){child=reinterpret_cast<uintptr_t>(motion);if(!read(motion,native,32))return;}
 else if(!read(motion,wrapper,64)||at<uint32_t>(wrapper,16)!=1||!read(at<void*>(wrapper,56),&handle,8)||!read((void*)(handle+32),&child,8)||!read((void*)child,native,32))return;
 if(!(at<uint32_t>(native,20)&0x80000000)||!read(at<void*>(native,24),source,48))return;
 capture(source,time);
 if(at<uint16_t>(source,8)==57&&candidates.size()<96){
  unsigned frames=at<uint16_t>(source,4);auto identity=std::make_pair((void*)child,frames);
  if(std::find(candidates.begin(),candidates.end(),identity)==candidates.end()){
   candidates.push_back(identity);std::ostringstream line;
   line<<"VICTORY CANDIDATE native="<<(void*)child<<" skeleton="<<skeleton<<" fps="<<at<float>(source,0)<<" frames="<<frames<<" time="<<time;
   log(line.str());
  }
 }
 for(auto& ref:references){auto p=ref.file.data();unsigned bones=at<uint16_t>(p,18)>>4;
  if(at<float>(source,0)!=at<float>(p,12)||at<uint16_t>(source,4)!=at<uint16_t>(p,16)||at<uint16_t>(source,8)!=bones)continue;
  auto keys=at<uint32_t>(p,20),vectors=at<uint32_t>(p,24);size_t packed=32+bones*4+keys;
  if(packed>ref.file.size()||packed+uint64_t(vectors)*32!=ref.file.size())continue;
  std::vector<unsigned char> table(bones*4),key(keys),data(size_t(vectors)*32);
  if(!read(at<void*>(source,24),table.data(),table.size())||!read(at<void*>(source,32),key.data(),key.size())||!read(at<void*>(source,40),data.data(),data.size()))continue;
  if(memcmp(table.data(),p+32,table.size())||memcmp(key.data(),p+32+table.size(),key.size())||memcmp(data.data(),p+packed,data.size()))continue;
  last=now;++samples;std::ostringstream line;line<<"VICTORY OBSERVER clip="<<ref.name<<" motion="<<motion<<" skeleton="<<skeleton<<" time="<<time<<" native="<<(void*)child<<" handle="<<(void*)handle;log(line.str());return;
 }
}
}

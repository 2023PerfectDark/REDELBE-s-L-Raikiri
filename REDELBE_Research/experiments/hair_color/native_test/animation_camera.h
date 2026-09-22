#pragma once
// Included inside animationpreviewtest. Files and samples are owned by us;
// game camera pointers are used only during native callbacks.
namespace camera {
struct File {std::vector<unsigned char> bytes;float seconds=0;uint64_t fingerprint=0;};
struct Selection {std::shared_ptr<File> dedicated;std::vector<uint64_t> anchors;};
struct Sample {float p[3]{},q[4]{0,0,0,1},distance=300,focus=1,extra=0,fov=45;};
using Motion=void(*)(void*,void*,void*,float);
using Commit=void(*)(void*,void*);
using Evaluate=uint32_t(*)(void*,int,float,void*);
static Motion apply=nullptr;static Commit commit=nullptr;static Evaluate evaluate=nullptr;
static std::shared_ptr<Selection> selection;
static std::atomic<bool> controls{},available{};
static std::atomic<ULONGLONG> updated{};
static std::mutex mutex;
static uintptr_t target=0;static ULONGLONG targetUntil=0;
struct Observed {uintptr_t object;uint64_t fingerprint;};
static std::vector<Observed> observed;
static bool freeValid=false;static Sample freeSample{};
static std::atomic<float> moveX{},moveY{},moveZ{},lookX{},lookY{},roll{},zoom{};
static std::atomic<bool> reset{};
static uint64_t hash(const unsigned char* p,size_t n){uint64_t h=14695981039346656037ull;for(size_t i=0;i<n;++i){h^=p[i];h*=1099511628211ull;}return h;}
static std::shared_ptr<File> load(const std::wstring& path){
 auto f=std::make_shared<File>();std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)return {};
 auto n=in.tellg();if(n<80||n>16*1024*1024)return {};f->bytes.resize(size_t(n));in.seekg(0);if(!in.read((char*)f->bytes.data(),n))return {};
 auto p=f->bytes.data();size_t size=f->bytes.size();if(memcmp(p,"_A1G2400",8)||uint64_t(at<uint32_t>(p,8))*16!=size)return {};
 f->seconds=at<float>(p,16);if(!std::isfinite(f->seconds)||f->seconds<=0||f->seconds>3600)return {};
 size_t table=(uint64_t(at<uint32_t>(p,32))+2)*16;if(table+16>size||at<uint32_t>(p,table)!=1)return {};
 auto relative=at<int32_t>(p,table+8);if(relative<1)return {};size_t track=table+uint64_t(relative)*16;
 if(track+4>size)return {};auto type=at<uint32_t>(p,track);unsigned channels=type==102?9:type==101?8:0;if(!channels||track+4+channels*8>size)return {};
 for(unsigned c=0;c<channels;++c){auto count=at<int32_t>(p,track+4+c*8),offset=at<int32_t>(p,track+8+c*8);
  if(count<1||count>100000||offset<1)return {};uint64_t coeff=track+uint64_t(offset)*16,times=coeff+uint64_t(count)*16;
  if(coeff<track+4+channels*8||times+uint64_t(count)*4>size)return {};
  float prev=0;for(int i=0;i<count;++i){float t=at<float>(p,size_t(times)+i*4);if(!std::isfinite(t)||t<=prev)return {};prev=t;for(int j=0;j<4;++j)if(!std::isfinite(at<float>(p,size_t(coeff)+i*16+j*4)))return {};}
 }
 f->fingerprint=hash(p,size);return f;
}
static void select(const std::wstring& root,const std::string& name,const std::string& character){
 auto s=std::make_shared<Selection>();std::ifstream in(root+L"cameras.tsv");std::string line;
 while(std::getline(in,line)){std::istringstream row(line);std::string key,rel;if(!std::getline(row,key,'\t')||!std::getline(row,rel))continue;if(!rel.empty()&&rel.back()=='\r')rel.pop_back();if(rel.rfind("Cameras/0x",0)!=0||rel.find("..")!=std::string::npos||rel.find(':')!=std::string::npos)continue;
  if(key==name||key=="@"+character){auto f=load(root+std::wstring(rel.begin(),rel.end()));if(!f)continue;if(key==name)s->dedicated=f;else s->anchors.push_back(f->fingerprint);}
 }
 std::lock_guard<std::mutex> guard(mutex);target=0;targetUntil=0;freeValid=false;updated=0;std::atomic_store(&selection,s);
}
static void observe(void* object,void* handle){
 if(!available)return;
 {std::lock_guard<std::mutex> guard(mutex);for(auto& o:observed)if(o.object==reinterpret_cast<uintptr_t>(object)){o.fingerprint=0;break;}}
 uintptr_t native=0,payload=0,vt=0,fn=0;unsigned char header[48]{};
 if(!read((unsigned char*)handle+32,&native,8)||!read((void*)native,&vt,8)||!read((void*)(vt+48),&fn,8)||fn!=reinterpret_cast<uintptr_t>(evaluate)||!read((void*)(native+16),&payload,8)||!read((void*)payload,header,48)||memcmp(header,"_A1G2400",8))return;
 auto size=uint64_t(at<uint32_t>(header,8))*16;if(size<80||size>16*1024*1024)return;std::vector<unsigned char> file(size);if(!read((void*)payload,file.data(),file.size()))return;
 auto fingerprint=hash(file.data(),file.size());std::lock_guard<std::mutex> guard(mutex);
 for(auto& o:observed)if(o.object==reinterpret_cast<uintptr_t>(object)){o.fingerprint=fingerprint;return;}
 if(observed.size()<64)observed.push_back({reinterpret_cast<uintptr_t>(object),fingerprint});
}
static bool snapshot(void* object,Sample& s){auto p=(unsigned char*)object;return read(p+0x2ea0,s.p,12)&&read(p+0x2eac,s.q,16)&&read(p+12,&s.distance,4)&&read(p+24,&s.focus,4)&&read(p+28,&s.extra,4)&&read(p+0x1f30,&s.fov,4);}
static bool valid(const Sample& s){for(float x:s.p)if(!std::isfinite(x)||fabs(x)>1000000)return false;float norm=0;for(float x:s.q){if(!std::isfinite(x))return false;norm+=x*x;}return norm>.8f&&norm<1.2f&&std::isfinite(s.distance)&&std::isfinite(s.focus)&&std::isfinite(s.extra)&&std::isfinite(s.fov);}
// Wardrobe places the preview at the scene origin. Use a level, full-body
// fight-style composition there, not the character-selection close-up.
// FOV is the native fighting-camera value captured during offline spectator.
// This is a fixed framing preset, not a retained pointer to a match camera.
static Sample fightingView(){Sample s{};s.p[0]=0;s.p[1]=92.5f;s.p[2]=400;
 s.q[0]=0;s.q[1]=1;s.q[2]=0;s.q[3]=0;
 s.distance=400;s.focus=0;s.extra=0;s.fov=.6195915f;return s;}
static void turn(float* q,float x,float y,float z,float angle){float h=angle*.5f,a[4]{x*sinf(h),y*sinf(h),z*sinf(h),cosf(h)},r[4];r[0]=a[3]*q[0]+a[0]*q[3]+a[1]*q[2]-a[2]*q[1];r[1]=a[3]*q[1]-a[0]*q[2]+a[1]*q[3]+a[2]*q[0];r[2]=a[3]*q[2]+a[0]*q[1]-a[1]*q[0]+a[2]*q[3];r[3]=a[3]*q[3]-a[0]*q[0]-a[1]*q[1]-a[2]*q[2];float n=sqrtf(r[0]*r[0]+r[1]*r[1]+r[2]*r[2]+r[3]*r[3]);for(int i=0;i<4;++i)q[i]=r[i]/n;}
static void axes(const float* q,float* right,float* up,float* back){float x=q[0],y=q[1],z=q[2],w=q[3];right[0]=1-2*(y*y+z*z);right[1]=2*(x*y+w*z);right[2]=2*(x*z-w*y);up[0]=2*(x*y-w*z);up[1]=1-2*(x*x+z*z);up[2]=2*(y*z+w*x);back[0]=2*(x*z+w*y);back[1]=2*(y*z-w*x);back[2]=1-2*(x*x+y*y);}
// Orbit around the Wardrobe model's torso rather than turning at a fixed eye.
// Rotate eye and orientation together, preserving radius and the current aim.
static void orbitAxis(Sample& s,float x,float y,float z,float angle){
 float v[3]{s.p[0],s.p[1]-92.5f,s.p[2]},c=cosf(angle),sn=sinf(angle),dot=x*v[0]+y*v[1]+z*v[2];
 float cross[3]{y*v[2]-z*v[1],z*v[0]-x*v[2],x*v[1]-y*v[0]},axis[3]{x,y,z};
 for(int i=0;i<3;++i)s.p[i]=v[i]*c+cross[i]*sn+axis[i]*dot*(1-c);
 s.p[1]+=92.5f;turn(s.q,x,y,z,angle);
}
static void orbit(Sample& s,float yaw,float pitch){
 orbitAxis(s,0,1,0,yaw);
 float right[3],up[3],back[3];axes(s.q,right,up,back);
 Sample candidate=s;orbitAxis(candidate,right[0],right[1],right[2],pitch);
 float x=candidate.p[0],y=candidate.p[1]-92.5f,z=candidate.p[2];
 float radius=sqrtf(x*x+y*y+z*z);
 // Keep orbit away from the poles; yaw remains usable at the pitch limit.
 if(radius>1 && fabs(y)/radius<.985f)s=candidate;
}
struct Native {void** vtable;float seconds;uint32_t pad;const Sample* sample;};
static bool isCamera(void*){return true;}
static uint32_t sample(void* p,int,float,void* output){memcpy(output,static_cast<Native*>(p)->sample,sizeof(Sample));return 0x789;}
static void send(void* object,void* manager,const Sample& s){void* methods[7]{};methods[4]=(void*)isCamera;methods[6]=(void*)sample;Native n{methods,3600,0,&s};alignas(16) unsigned char handle[40]{};put(handle,32,&n);apply(object,manager,handle,0);}
static void commitFrame(void* object,void* manager){
 if(!available||!expanded||!active||GetTickCount64()>wardrobeUntil||GetTickCount64()-appliedAt.load()>250){commit(object,manager);return;}
 std::unique_lock<std::mutex> guard(mutex);auto now=GetTickCount64();auto s=std::atomic_load(&selection);
 bool matched=false;if(s)for(auto& o:observed)if(o.object==reinterpret_cast<uintptr_t>(object)&&std::find(s->anchors.begin(),s->anchors.end(),o.fingerprint)!=s->anchors.end()){matched=true;break;}
 if(!matched){guard.unlock();commit(object,manager);return;}
 if(target!=reinterpret_cast<uintptr_t>(object)){target=reinterpret_cast<uintptr_t>(object);log("ANIMATION CAMERA bound to matching character-selection camera");}
 Sample baseline;if(!snapshot(object,baseline)||!valid(baseline)){guard.unlock();commit(object,manager);return;}Sample desired=baseline;
 if(!controls&&s->dedicated){auto body=std::atomic_load(&selected);if(body){float t=paused?position.load():float(fmod(position.load()+(now-started.load())/1000.,body->seconds));alignas(16) unsigned char n[32]{};void* methods[7]{}; // Only count (+8) is read by the verified evaluator.
   methods[1]=(void*)+[](void*)->unsigned{return 1;};put(n,0,methods);put(n,8,s->dedicated->seconds);put(n,16,s->dedicated->bytes.data());put<uint32_t>(n,24,0x80018000);
   alignas(16) unsigned char output[128]{};auto mask=evaluate(n,0,std::min(t,s->dedicated->seconds),output);if((mask&9)==9){memcpy(desired.p,output,12);memcpy(desired.q,output+12,16);if(mask&128)desired.distance=at<float>(output,28);if(mask&256)desired.focus=at<float>(output,32);if(mask&512)desired.extra=at<float>(output,36);if(mask&1024)desired.fov=at<float>(output,40);}
  }freeValid=false;
 }else if(controls){
  if(!freeValid||reset.exchange(false)){freeSample=s->dedicated?baseline:fightingView();freeValid=true;}
  float right[3],up[3],back[3];axes(freeSample.q,right,up,back);float x=moveX.exchange(0),y=moveY.exchange(0),z=moveZ.exchange(0);
  for(int i=0;i<3;++i)freeSample.p[i]+=right[i]*x+up[i]*y+back[i]*z;
  orbit(freeSample,lookX.exchange(0),lookY.exchange(0));axes(freeSample.q,right,up,back);turn(freeSample.q,back[0],back[1],back[2],roll.exchange(0));
  freeSample.fov=std::max(.08f,std::min(3.f,freeSample.fov+zoom.exchange(0)));desired=freeSample;
 }else{desired=fightingView();freeValid=false;}
 if(!valid(desired)){guard.unlock();commit(object,manager);return;}
 send(object,manager,desired);commit(object,manager);send(object,manager,baseline);updated=now;
}
static void input(const XINPUT_GAMEPAD& g,float dt){auto axis=[](SHORT v){float f=v/32767.f;return fabs(f)<.18f?0.f:f;};bool y=(g.wButtons&XINPUT_GAMEPAD_Y)!=0;
 moveX=moveX.load()+axis(g.sThumbLX)*dt*120; if(y)moveZ=moveZ.load()-axis(g.sThumbLY)*dt*180;else moveY=moveY.load()+axis(g.sThumbLY)*dt*120;
 lookX=lookX.load()-axis(g.sThumbRX)*dt;lookY=lookY.load()+axis(g.sThumbRY)*dt;roll=roll.load()+(g.bRightTrigger-g.bLeftTrigger)/255.f*dt;
 if(!y){float direction=(g.wButtons&XINPUT_GAMEPAD_DPAD_UP)?-1.f:(g.wButtons&XINPUT_GAMEPAD_DPAD_DOWN)?1.f:0.f;zoom=zoom.load()+direction*dt*.4f;}
 if(g.wButtons&XINPUT_GAMEPAD_RIGHT_THUMB)reset=true;
}
}


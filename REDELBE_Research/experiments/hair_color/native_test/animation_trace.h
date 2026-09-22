#pragma once
#include "victory_observer.h"
// Native evaluator integration with optional bounded diagnostics.
namespace animationtrace {
using CameraState=void(*)(void*,void*);
using CameraMotion=void(*)(void*,void*,void*,float);
static CameraState nativeCameraStateOriginal=nullptr;
static CameraMotion nativeCameraMotionOriginal=nullptr;
static animationpreviewtest::camera::Commit nativeCameraCommitOriginal=nullptr;
static bool nativeCameraTracing=false;
static void nativeCameraCommitHook(void* camera,void* manager){
 animationpreviewtest::camera::apply=nativeCameraMotionOriginal;
 animationpreviewtest::camera::commit=nativeCameraCommitOriginal;
 animationpreviewtest::camera::commitFrame(camera,manager);
}
static std::mutex nativeCameraMutex;
struct NativeCameraSample {void* camera; uintptr_t caller; ULONGLONG last;};
static std::vector<NativeCameraSample> nativeCameraSamples;
static unsigned nativeCameraCount=0;
static void recordNativeCamera(void* camera,uintptr_t caller,void* motion=nullptr,float time=0) {
 if(!nativeCameraTracing)return;
 std::unique_lock<std::mutex> lock(nativeCameraMutex,std::try_to_lock);
 if(!lock.owns_lock()||nativeCameraCount>=512)return;
 auto now=GetTickCount64();bool known=false;
 for(auto& s:nativeCameraSamples)if(s.camera==camera&&s.caller==caller){if(now-s.last<2000)return;s.last=now;known=true;break;}
 if(!known){if(nativeCameraSamples.size()>=64)return;nativeCameraSamples.push_back({camera,caller,now});}
 ++nativeCameraCount;
 float transform[7]{};SIZE_T got=0;
 if(!ReadProcessMemory(GetCurrentProcess(),static_cast<unsigned char*>(camera)+0x2ea0,transform,sizeof(transform),&got)||got!=sizeof(transform))return;
 std::ostringstream line;line<<"NATIVE CAMERA camera="<<camera<<" caller_rva="<<std::hex<<(caller-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)))<<std::dec<<" motion="<<motion<<" time="<<time<<" transform=";
 for(float value:transform)line<<value<<",";
 log(line.str());
}
static void nativeCameraStateHook(void* camera,void* output) {
 nativeCameraStateOriginal(camera,output);
 recordNativeCamera(camera,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
static void nativeCameraMotionHook(void* camera,void* manager,void* motion,float time) {
 animationpreviewtest::camera::observe(camera,motion);
 recordNativeCamera(camera,reinterpret_cast<uintptr_t>(_ReturnAddress()),motion,time);
 nativeCameraMotionOriginal(camera,manager,motion,time);
}
using Function=uintptr_t(*)(void*);
static Function modelOriginal=nullptr,cameraOriginal=nullptr,actionOriginal=nullptr;
static std::atomic<unsigned> counts[3]{};
static std::atomic<ULONGLONG> last[3]{};
static void record(unsigned kind,void* context) {
 auto now=GetTickCount64(),previous=last[kind].load();
 if(now-previous<500||counts[kind]>=1200||!last[kind].compare_exchange_strong(previous,now))return;
 ++counts[kind];unsigned char data[128]{};SIZE_T got=0;
 if(!ReadProcessMemory(GetCurrentProcess(),context,data,sizeof(data),&got))return;
 std::ostringstream line;line<<"ANIMATION TRACE "<<(kind==2?"action-camera":kind?"camera":"model")<<" context="<<context<<" bytes=";
 const char* digits="0123456789abcdef";for(SIZE_T i=0;i<got;++i){line<<digits[data[i]>>4]<<digits[data[i]&15];}
 log(line.str());
}
static uintptr_t modelHook(void* context){record(0,context);return modelOriginal(context);}
static uintptr_t actionHook(void* context){record(2,context);return actionOriginal(context);}
static uintptr_t cameraHook(void* context){record(1,context);return cameraOriginal(context);}
// Native skeletal evaluator: optional owned preview data is held through the call.
// Captures are bounded and never retain resource pointers for later playback.
using Evaluate=void(*)(void*,void*,void*,float,void*,void*,void*,void*);
static Evaluate evaluateOriginal=nullptr;
static std::atomic<unsigned> evaluateCount{};
static bool evaluationTracing=false;
struct EvaluationSample { void* motion; void* skeleton; ULONGLONG last; };
static std::mutex evaluateMutex;
static std::vector<EvaluationSample> evaluateSamples;
static bool shouldRecordEvaluation(void* motion,void* skeleton,ULONGLONG now) {
 std::unique_lock<std::mutex> lock(evaluateMutex,std::try_to_lock);
 if(!lock.owns_lock()||evaluateCount>=4096)return false;
 for(auto& sample:evaluateSamples)if(sample.motion==motion&&sample.skeleton==skeleton){
  if(now-sample.last<2000)return false;
  sample.last=now;++evaluateCount;return true;
 }
 if(evaluateSamples.size()>=128)return false;
 evaluateSamples.push_back({motion,skeleton,now});++evaluateCount;return true;
}
static void evaluateHook(void* motion,void* manager,void* skeleton,float time,void* a5,void* a6,void* a7,void* a8) {
 victoryobserver::observe(motion,skeleton,time);
 auto caller=reinterpret_cast<uintptr_t>(_ReturnAddress());
 if(evaluationTracing&&shouldRecordEvaluation(motion,skeleton,GetTickCount64())) {
  unsigned char data[128]{};SIZE_T got=0;
  std::ostringstream line;line<<"ANIMATION EVALUATE motion="<<motion<<" manager="<<manager<<" skeleton="<<skeleton<<" time="<<time<<" bytes=";
  if(ReadProcessMemory(GetCurrentProcess(),motion,data,sizeof(data),&got)) {
   const char* digits="0123456789abcdef";for(SIZE_T i=0;i<got;++i)line<<digits[data[i]>>4]<<digits[data[i]&15];
  }
  line<<" caller_rva="<<std::hex<<(caller-reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)))
      <<" options="<<a5<<" blend="<<a6;
  log(line.str());
 }
 alignas(16) unsigned char native[32]{};
 std::shared_ptr<animationpreviewtest::Clip> keep;
 if(animationpreviewtest::substitute(motion,native,time,keep))motion=native;
 evaluateOriginal(motion,manager,skeleton,time,a5,a6,a7,a8);
}
// Direct facial evaluator, with exact bone-list validation and owned clip lifetime.
using EvaluateDirect=void(*)(void*,void*,void*,float,void*,void*);
static EvaluateDirect evaluateDirectOriginal=nullptr;
static void evaluateDirectHook(void* motion,void* manager,void* skeleton,float time,void* options,void* output){
 victoryobserver::observe(motion,skeleton,time,true);
 if(evaluationTracing&&shouldRecordEvaluation(motion,skeleton,GetTickCount64())){
  std::ostringstream line;line<<"ANIMATION EVALUATE motion="<<motion<<" manager="<<manager<<" skeleton="<<skeleton<<" time="<<time<<" direct=1";log(line.str());
 }
 alignas(16) unsigned char native[32]{};std::shared_ptr<animationpreviewtest::Clip> keep;
 bool replaced=animationpreviewtest::substituteFace(motion,native,time,keep);
 if(replaced)motion=native;
 unsigned char faceHeader[32]{},facePayload[48]{};
 bool facialCall=animationpreviewtest::read(motion,faceHeader,32)&&animationpreviewtest::read(animationpreviewtest::at<void*>(faceHeader,24),facePayload,48)&&animationpreviewtest::at<uint16_t>(facePayload,8)==344;
 if(animationpreviewtest::active&&facialCall){
  static std::atomic<ULONGLONG> reported{};auto now=GetTickCount64(),last=reported.load();
  if(now-last>2000&&reported.compare_exchange_strong(last,now)){
   auto clip=std::atomic_load(&animationpreviewtest::selectedFace);std::ostringstream line;
   line<<"FACIAL PLAYBACK applied="<<replaced<<" clip="<<(clip?clip->bones:0)<<" time="<<time<<" wardrobe="<<(now<=animationpreviewtest::wardrobeUntil)<<" skeleton="<<skeleton;log(line.str());
  }
 }
 evaluateDirectOriginal(motion,manager,skeleton,time,options,output);
}

// Native resource evaluation entry, shared by the higher-level playback paths.
// The facial compositor samples the motion again after scratch evaluation.
// Keep the owned facial resource alive through that final per-bone sample too.
using FaceBone=bool(*)(void*,void*,float,unsigned,void*,float,void*,bool);
static FaceBone faceBoneOriginal=nullptr;
static bool faceBoneHook(void* output,void* motion,float time,unsigned bone,void* rig,float weight,void* context,bool relative){
 alignas(16) unsigned char native[32]{};std::shared_ptr<animationpreviewtest::Clip> keep;
 float replacementTime=time;
 bool replace=animationpreviewtest::substituteFace(motion,native,replacementTime,keep);
 if(!replace)replace=animationpreviewtest::substitute(motion,native,replacementTime,keep)&&keep&&keep->bones==344;
 if(replace){motion=native;time=replacementTime;}
 return faceBoneOriginal(output,motion,time,bone,rig,weight,context,relative);
}
using EvaluateResource=void(*)(void*,void*,void*,float,float,float,unsigned,bool,void*,void*);
static EvaluateResource evaluateResourceOriginal=nullptr;
static void evaluateResourceHook(void* motion,void* manager,void* skeleton,float weight,float time,float rate,unsigned cycles,bool reverse,void* context,void* mask){
 victoryobserver::observe(motion,skeleton,time,true);
 alignas(16) unsigned char native[32]{};std::shared_ptr<animationpreviewtest::Clip> keep;
 bool replaced=animationpreviewtest::substituteFace(motion,native,time,keep);
 if(replaced)motion=native;
 evaluateResourceOriginal(motion,manager,skeleton,weight,time,rate,cycles,reverse,context,mask);
 if(replaced&&evaluationTracing){
  static std::atomic<ULONGLONG> reported{};auto now=GetTickCount64(),last=reported.load();
  if(now-last>1000&&reported.compare_exchange_strong(last,now)){
   using namespace animationpreviewtest;
   unsigned char sk[48]{},rig[16]{},header[12]{};
   if(read(skeleton,sk,sizeof(sk))&&read(at<void*>(sk,8),rig,sizeof(rig))&&read(at<void*>(rig,0),header,sizeof(header))){
    int count=at<int16_t>(header,6);std::ostringstream line;
    line<<"FACIAL OUTPUT skeleton="<<skeleton<<" time="<<time<<" weight="<<weight<<" count="<<count<<" mask="<<mask;
    for(int bid:{136,143,249,383})if(bid<count&&count<4096){
     int16_t index=-1;auto ids=static_cast<unsigned char*>(at<void*>(rig,0));
     if(read(ids+12+bid*2,&index,2)&&index>=0&&index<4096){
      float values[12]{};auto output=static_cast<unsigned char*>(at<void*>(sk,32));
      if(read(output+index*48,values,sizeof(values))){line<<" bone="<<bid<<":";for(float v:values)line<<v<<",";}
     }
    }
    log(line.str());
   }else log("FACIAL OUTPUT skeleton header unavailable");
  }
 }
}

}

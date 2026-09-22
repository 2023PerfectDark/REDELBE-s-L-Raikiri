#pragma once
#include <mmsystem.h>
#include <array>
#include <cmath>
#include "aura_sound_patterns.h"
#pragma comment(lib,"winmm.lib")
namespace aurasound {
static std::mutex stateMutex;static void* weakControls[2]{};static unsigned generation=0;
static uintptr_t volumeCell=0,pauseCell=0;static bool enabled=false;static float multiplier=1;
static std::vector<short> samples;static WAVEFORMATEX format{};
static std::atomic<bool> stopping{false};
static HANDLE workerThread=nullptr;
// Called before ExitProcess begins CRT/native-object teardown. Never join from
// DllMain: the worker needs Windows APIs while releasing its audio device.
static void shutdown(){
 stopping.store(true);
 if(workerThread&&GetThreadId(workerThread)!=GetCurrentThreadId()){
  if(WaitForSingleObject(workerThread,2000)==WAIT_OBJECT_0){CloseHandle(workerThread);workerThread=nullptr;}
 }
}
// The audio worker can outlive native battle objects during teardown. A weak
// control address is not permission to perform an interlocked write through it.
static bool readStrongCount(void* control,LONG& count){
 SIZE_T got=0;count=0;
 return control&&ReadProcessMemory(GetCurrentProcess(),static_cast<BYTE*>(control)+8,
     &count,sizeof(count),&got)&&got==sizeof(count);
}
static void track(void* control,unsigned side=0){
 if(!enabled||stopping.load()||!control||side>1)return;
 std::lock_guard<std::mutex> guard(stateMutex);
 InterlockedIncrement(reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(control)+12));
 auto previous=weakControls[side];weakControls[side]=control;
 LONG otherCount=0;if(!readStrongCount(weakControls[1-side],otherCount)||otherCount<=0)++generation;
 if(previous&&InterlockedDecrement(reinterpret_cast<volatile LONG*>(static_cast<BYTE*>(previous)+12))==0){auto v=*reinterpret_cast<void***>(previous);reinterpret_cast<void(*)(void*)>(v[1])(previous);}
}
static bool active(unsigned& serial){std::lock_guard<std::mutex> guard(stateMutex);serial=generation;for(auto& control:weakControls){LONG count=0;if(!control)continue;if(!readStrongCount(control,count)){control=nullptr;log("AURA SOUND retired inaccessible native control");continue;}if(count>0)return true;}return false;}
static float gameSe(){
 __try {auto controller=*reinterpret_cast<BYTE**>(volumeCell);if(!controller)return 0;float v=*reinterpret_cast<float*>(controller+0x148);return v>=0&&v<=1?v:0;}
 __except(EXCEPTION_EXECUTE_HANDLER){return 0;}
}
static bool battlePaused(){
 __try {auto state=*reinterpret_cast<BYTE**>(pauseCell);if(!state)return true;return ((*reinterpret_cast<volatile unsigned*>(state+0x510)|*reinterpret_cast<volatile unsigned*>(state+0x514))&4)!=0;}
 __except(EXCEPTION_EXECUTE_HANDLER){return true;}
}
static unsigned u32(const BYTE* p){unsigned v;memcpy(&v,p,4);return v;}
static unsigned u16(const BYTE* p){unsigned short v;memcpy(&v,p,2);return v;}
static void loadWav(const std::wstring& path){
 std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)throw std::runtime_error("sound WAV not found");auto size=in.tellg();if(size<44||size>24*1024*1024)throw std::runtime_error("WAV size invalid");
 std::vector<BYTE> bytes(static_cast<size_t>(size));in.seekg(0);if(!in.read(reinterpret_cast<char*>(bytes.data()),bytes.size()))throw std::runtime_error("WAV read failed");
 if(memcmp(bytes.data(),"RIFF",4)||memcmp(bytes.data()+8,"WAVE",4)||uint64_t(u32(bytes.data()+4))+8>bytes.size())throw std::runtime_error("not a RIFF WAV");
 size_t dataAt=0,dataSize=0;bool fmt=false;size_t limit=size_t(u32(bytes.data()+4))+8;
 for(size_t p=12;p+8<=limit;){size_t n=u32(bytes.data()+p+4);if(n>limit-p-8)throw std::runtime_error("truncated WAV chunk");auto chunk=bytes.data()+p+8;
  if(!memcmp(bytes.data()+p,"fmt ",4)){if(n<16||u16(chunk)!=1||u16(chunk+14)!=16)throw std::runtime_error("use PCM 16-bit WAV");format.wFormatTag=WAVE_FORMAT_PCM;format.nChannels=static_cast<WORD>(u16(chunk+2));format.nSamplesPerSec=u32(chunk+4);format.nBlockAlign=static_cast<WORD>(u16(chunk+12));format.wBitsPerSample=16;format.nAvgBytesPerSec=u32(chunk+8);fmt=true;}
  if(!memcmp(bytes.data()+p,"data",4)){dataAt=p+8;dataSize=n;}p+=8+n+(n&1);
 }
 if(!fmt||!dataSize||format.nChannels<1||format.nChannels>2||format.nSamplesPerSec<8000||format.nSamplesPerSec>96000||format.nBlockAlign!=format.nChannels*2||format.nAvgBytesPerSec!=format.nSamplesPerSec*format.nBlockAlign||dataSize%format.nBlockAlign||dataSize>format.nAvgBytesPerSec*60u)throw std::runtime_error("unsupported WAV layout (mono/stereo PCM16, maximum 60 seconds)");
 samples.resize(dataSize/2);memcpy(samples.data(),bytes.data()+dataAt,dataSize);
}
static DWORD WINAPI worker(void*){
 HANDLE event=CreateEventW(nullptr,FALSE,FALSE,nullptr);if(!event){log("AURA SOUND event failed");return 0;}
 HWAVEOUT device=nullptr;auto result=waveOutOpen(&device,WAVE_MAPPER,&format,reinterpret_cast<DWORD_PTR>(event),0,CALLBACK_EVENT);
 if(result!=MMSYSERR_NOERROR){log("AURA SOUND output unavailable error="+std::to_string(result));CloseHandle(event);return 0;}
 const size_t count=size_t(format.nSamplesPerSec/20)*format.nChannels;
 struct Buffer{WAVEHDR header{};std::vector<short> pcm;bool queued=false;};std::array<Buffer,3> buffers;
 unsigned prepared=0;bool valid=true;
 for(auto& b:buffers){b.pcm.resize(count);b.header.lpData=reinterpret_cast<char*>(b.pcm.data());b.header.dwBufferLength=static_cast<DWORD>(count*2);if(waveOutPrepareHeader(device,&b.header,sizeof(WAVEHDR))!=MMSYSERR_NOERROR){valid=false;break;}++prepared;}
 log("AURA SOUND output ready; PCM loop follows Game SE");
 bool playing=false,paused=false;unsigned seen=0;size_t cursor=0;float previousGain=0;
 while(valid&&!stopping.load()){
  unsigned serial;bool wanted=active(serial);
  if(playing&&(!wanted||serial!=seen)){waveOutReset(device);for(auto& b:buffers)b.queued=false;playing=false;paused=false;cursor=0;previousGain=0;log("AURA SOUND stopped");}
  if(wanted){
   if(!playing){playing=true;seen=serial;log("AURA SOUND loop started");}
   bool pauseNow=battlePaused();
   if(pauseNow!=paused){auto error=pauseNow?waveOutPause(device):waveOutRestart(device);if(error!=MMSYSERR_NOERROR){log("AURA SOUND pause/resume failed error="+std::to_string(error));valid=false;break;}paused=pauseNow;log(paused?"AURA SOUND paused":"AURA SOUND resumed");}
   if(paused){WaitForSingleObject(event,20);continue;}
   for(auto& b:buffers){if(b.queued&&!(b.header.dwFlags&WHDR_DONE))continue;float gain=gameSe()*multiplier;
    size_t frames=count/format.nChannels;
    for(size_t i=0;i<count;++i){float t=float(i/format.nChannels+1)/float(frames);float g=previousGain+(gain-previousGain)*t;b.pcm[i]=static_cast<short>(std::lround(samples[cursor]*g));cursor=(cursor+1)%samples.size();}
    previousGain=gain;auto error=waveOutWrite(device,&b.header,sizeof(WAVEHDR));if(error!=MMSYSERR_NOERROR){log("AURA SOUND write failed error="+std::to_string(error));valid=false;break;}b.queued=true;
   }
  }
  WaitForSingleObject(event,20);
 }
 waveOutReset(device);for(unsigned i=0;i<prepared;++i)waveOutUnprepareHeader(device,&buffers[i].header,sizeof(WAVEHDR));waveOutClose(device);CloseHandle(event);return 0;
}
static void install(){
 if(!userconfig::current.flag("AuraSound","enabled"))return;
 auto base=reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));auto nt=reinterpret_cast<IMAGE_NT_HEADERS64*>(base+reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];auto funcs=reinterpret_cast<RUNTIME_FUNCTION*>(base+dir.VirtualAddress);BYTE* hit=nullptr;
 for(unsigned i=0;i<dir.Size/sizeof(*funcs);++i){auto f=funcs[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress-f.BeginAddress!=auraGameSePattern.size)continue;if(gamecode::match(base+f.BeginAddress,auraGameSePattern)){if(hit)throw std::runtime_error("Game SE pattern ambiguous");hit=base+f.BeginAddress;}}
 if(!hit||memcmp(hit+0x46,"\x48\x8b\x0d",3)||memcmp(hit+0x95,"\xf3\x0f\x11\xb1\x48\x01\x00\x00",8))throw std::runtime_error("Game SE pattern not recognized");
 int32_t d;memcpy(&d,hit+0x49,4);volumeCell=reinterpret_cast<uintptr_t>(hit+0x4d+d);
 auto findFunction=[&](const GamePattern& pattern)->BYTE*{BYTE* found=nullptr;for(unsigned i=0;i<dir.Size/sizeof(*funcs);++i){auto f=funcs[i];if(f.EndAddress>nt->OptionalHeader.SizeOfImage||f.EndAddress-f.BeginAddress!=pattern.size)continue;if(gamecode::match(base+f.BeginAddress,pattern)){if(found)throw std::runtime_error("pause pattern ambiguous");found=base+f.BeginAddress;}}if(!found)throw std::runtime_error("pause pattern not recognized");return found;};
 auto pause=findFunction(auraPausePattern);
 BYTE* resume=nullptr;for(unsigned i=0;i<dir.Size/sizeof(*funcs);++i){auto f=funcs[i];if(f.EndAddress<=nt->OptionalHeader.SizeOfImage&&f.EndAddress-f.BeginAddress==auraResumePattern.size&&gamecode::match(base+f.BeginAddress,auraResumePattern)){int32_t rd0,pd0;memcpy(&rd0,base+f.BeginAddress+0x13,4);memcpy(&pd0,pause+0x41,4);if(base+f.BeginAddress+0x17+rd0==pause+0x45+pd0)resume=base+f.BeginAddress;}}
 if(!resume)throw std::runtime_error("pause/resume state roots disagree");
 int32_t pd,rd;memcpy(&pd,pause+0x41,4);memcpy(&rd,resume+0x13,4);
 auto pc=reinterpret_cast<uintptr_t>(pause+0x45+pd),rc=reinterpret_cast<uintptr_t>(resume+0x17+rd);
 if(pc!=rc)throw std::runtime_error("pause/resume state roots disagree");pauseCell=pc;
 multiplier=userconfig::current.number("AuraSound","volume")/100.f;
 auto rel=wide(userconfig::current.text("AuraSound","file"));if(rel.empty()||rel.find(L":")!=std::wstring::npos||rel[0]==L'\\'||rel[0]==L'/'||rel.find(L"..")!=std::wstring::npos)throw std::runtime_error("sound path must be relative to REDELBE_LR");
 loadWav(gameRoot+L"REDELBE_LR\\"+rel);
 HMODULE pin=nullptr;if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&worker),&pin))throw std::runtime_error("sound module pin failed");
 stopping.store(false);enabled=true;workerThread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(!workerThread){enabled=false;throw std::runtime_error("sound thread failed");}
 log("AURA SOUND configured file="+utf8(rel)+" volume="+std::to_string(static_cast<int>(multiplier*100)));
}
}

from pathlib import Path
p=Path(__file__).resolve().parents[1]/'experiments/hair_color/native_test/animation_preview_test.h'
s=p.read_text()
s=s.replace('#include <cmath>','#include <cmath>\n#include <memory>\n#pragma comment(lib,"gdi32.lib")')
s=s.replace('static std::vector<unsigned char> file,payload;','struct Clip {std::vector<unsigned char> file,payload;float seconds=0;uint16_t bones=0;};\nstatic std::shared_ptr<Clip> selected;\nstatic std::atomic<bool> expanded{},paused{};\nstatic std::atomic<float> position{};\nstatic std::atomic<ULONGLONG> appliedAt{};')
s=s.replace('static float seconds=0;\nstatic uint16_t bones=0;','')
s=s.replace('static void initialize(const std::wstring& path){','static bool loadClip(const std::wstring& path){\n auto clip=std::make_shared<Clip>();auto& file=clip->file;auto& payload=clip->payload;auto& bones=clip->bones;auto& seconds=clip->seconds;')
a=s.index('static bool loadClip');b=s.index('static void poll',a)
parse=s[a:b].replace('return;','return false;')
parse=parse.replace('seconds=frames/fps;ready=true;log("ANIMATION PREVIEW TEST clip validated; F8 arms only in Wardrobe");','seconds=frames/fps;std::atomic_store(&selected,clip);ready=true;position=0;started=GetTickCount64();paused=false;appliedAt=0;return true;')
s=s[:a]+parse+s[b:]
a=s.index('static void poll');b=s.index('static bool substitute',a)
s=s[:a]+'#include "animation_browser_ui.h"\n'+s[b:]
s=s.replace('static bool substitute(void* motion,unsigned char* native,float& time){','static bool substitute(void* motion,unsigned char* native,float& time,std::shared_ptr<Clip>& keep){')
s=s.replace('if(!ready||!active||GetTickCount64()>wardrobeUntil)return false;','if(!active||GetTickCount64()>wardrobeUntil)return false;\n keep=std::atomic_load(&selected);if(!keep)return false;auto& file=keep->file;auto& payload=keep->payload;auto bones=keep->bones;auto seconds=keep->seconds;')
s=s.replace('time=static_cast<float>(std::fmod((GetTickCount64()-started.load())/1000.0,seconds));return true;','time=paused?position.load():static_cast<float>(std::fmod(position.load()+(GetTickCount64()-started.load())/1000.0,seconds));appliedAt=GetTickCount64();return true;')
p.write_text(s)
p=p.with_name('animation_trace.h');s=p.read_text().replace('// Optional local diagnostics. No animation substitution or retained VM pointers.','// Native evaluator integration with optional bounded diagnostics.').replace('// Native skeletal evaluator: all eight arguments are forwarded unchanged.','// Native skeletal evaluator: optional owned preview data is held through the call.')
s=s.replace('if(shouldRecordEvaluation(motion,skeleton,GetTickCount64()))','if(!animationpreviewtest::expanded&&shouldRecordEvaluation(motion,skeleton,GetTickCount64()))')
s=s.replace('if(animationpreviewtest::substitute(motion,native,time))','std::shared_ptr<animationpreviewtest::Clip> keep;\n if(animationpreviewtest::substitute(motion,native,time,keep))');p.write_text(s)

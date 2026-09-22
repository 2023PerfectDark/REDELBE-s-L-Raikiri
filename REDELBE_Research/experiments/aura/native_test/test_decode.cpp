#define wWinMain unusedVideoMain
#include "video_preview.cpp"
#include <cassert>
int wmain(int argc,wchar_t** argv) {
 assert(argc==3);assert(SUCCEEDED(CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED)));
 auto randomRoot=std::filesystem::path(argv[1]).parent_path()/L"random_selection_test";
 auto randomDir=randomRoot/L"Random Vanilla Stage-Modded Stage";
 std::filesystem::create_directories(randomDir);
 std::filesystem::copy_file(argv[1],randomDir/L"one.mp4",std::filesystem::copy_options::overwrite_existing);
 std::filesystem::copy_file(argv[1],randomDir/L"two.MP4",std::filesystem::copy_options::overwrite_existing);
 auto chosen=randomPreview(randomRoot.wstring(),L"");assert(!chosen.empty());
 auto next=randomPreview(randomRoot.wstring(),chosen);assert(!next.empty()&&next!=chosen);
 assert(randomPreview((randomRoot/L"missing").wstring(),L"").empty());
 assert(SUCCEEDED(MFStartup(MF_VERSION)));
 {
  Video v;assert(!v.open(L"missing-preview-test.mp4"));
  assert(v.open(argv[1]));assert(v.width==320&&v.height==180);
  unsigned frames=0;auto now=GetTickCount64();
  for(unsigned i=0;i<200;++i){bool updated=false;assert(v.frame(now+i*40,updated));if(updated)++frames;}
  assert(frames>60); // Includes EOF rewind and a second loop.
  assert(v.pixels.size()==320*180*4);
  PreviewAudio audio;
  assert(!audio.open(argv[1],0)); // Video-only file must not request music ducking.
  assert(audio.open(argv[2],0));assert(audio.pump());
  audio.rewind();assert(audio.pump());audio.close();assert(!audio.pump());
 }
 MFShutdown();CoUninitialize();return 0;
}

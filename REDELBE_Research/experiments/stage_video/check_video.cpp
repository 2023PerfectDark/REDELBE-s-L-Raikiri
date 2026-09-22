#define wWinMain unusedPreviewMain
#include "video_preview.cpp"
#include <iostream>
int wmain(int argc,wchar_t** argv) {
 if(argc!=2)return 1;CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);MFStartup(MF_VERSION);
 Video video;if(!video.open(argv[1])){std::cout<<"open failed\n";return 2;}
 auto now=GetTickCount64();unsigned frames=0,loops=0;LONGLONG maxStamp=0;
 bool saved=false;
 for(unsigned i=0;i<20000&&loops<2;++i){bool updated=false;if(!video.frame(now+i*40,updated)){std::cout<<"decode failed timestamp="<<video.stamp<<"\n";return 3;}if(updated){++frames;maxStamp=std::max(maxStamp,video.stamp);
 if(!saved&&video.stamp>=30000000){std::ofstream out("experiments/stage_video/build/native_frame.ppm",std::ios::binary);out<<"P6\n"<<video.width<<" "<<video.height<<"\n255\n";for(size_t j=0;j<video.pixels.size();j+=4){char rgb[]={char(video.pixels[j+2]),char(video.pixels[j+1]),char(video.pixels[j])};out.write(rgb,3);}saved=true;std::cout<<"stride="<<video.stride<<"\n";}
 }if(video.looped)++loops;}
 std::cout<<"frames="<<frames<<" loops="<<loops<<" final_seconds="<<maxStamp/10000000.0<<"\n";
 video.close();MFShutdown();CoUninitialize();return loops==2?0:4;
}

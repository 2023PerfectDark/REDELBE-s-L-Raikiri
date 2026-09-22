#pragma once
#include <string>
#include <vector>
#include <cstdint>
namespace noticescroll {
// Pixel-space timing for the clipped renderer. Keep fractional positions:
// rounding here would reintroduce visible steps at slow speeds.
static double pixelOffset(uint64_t elapsed,double contentHeight,double viewportHeight,double pixelsPerSecond=12.0){
 if(contentHeight<=viewportHeight||pixelsPerSecond<=0)return 0;
 const double distance=contentHeight-viewportHeight;
 const double travel=distance*1000.0/pixelsPerSecond;
 const double cycle=6000.0+travel;
 const double t=double(elapsed)-double(uint64_t(double(elapsed)/cycle))*cycle;
 if(t<=3000.0)return 0;
 const double value=(t-3000.0)*pixelsPerSecond/1000.0;
 return value<distance?value:distance;
}
static std::vector<std::wstring> wrap(const std::wstring& text,size_t width=64){
 std::vector<std::wstring> out;size_t start=0;
 while(start<text.size()){
  auto end=text.find(L'\n',start);if(end==std::wstring::npos)end=text.size();
  auto line=text.substr(start,end-start);if(!line.empty()&&line.back()==L'\r')line.pop_back();
  while(line.size()>width){auto cut=line.rfind(L' ',width);if(cut==std::wstring::npos||cut==0)cut=width;out.push_back(line.substr(0,cut));line.erase(0,cut);if(!line.empty()&&line.front()==L' ')line.erase(0,1);}
  out.push_back(line);start=end+1;
 }return out;
}
static std::wstring frame(const std::wstring& text,uint64_t elapsed,unsigned interval,unsigned visible,bool enabled){
 auto lines=wrap(text);if(!enabled||lines.size()<=visible+1)return text;
 interval=interval<300?300:interval;visible=visible<2?2:visible;
 const size_t steps=lines.size()-1-visible;
 const uint64_t travel=uint64_t(steps)*interval,cycle=6000+travel;
 const uint64_t t=elapsed%cycle;
 const size_t offset=t<3000?0:static_cast<size_t>((t-3000)/interval>steps?steps:(t-3000)/interval);
 std::wstring out=lines[0]+L"\n";
 for(size_t i=0;i<visible;++i){if(i)out+=L"\n";out+=lines[1+offset+i];}
 return out;
}
}

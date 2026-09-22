#pragma once
#include <objidl.h>
#include <gdiplus.h>
#pragma comment(lib,"gdiplus.lib")
namespace noticedisplay {
static std::atomic<bool> started{},visible{};
static std::atomic<HWND> owner{};
static std::mutex mutex;
static std::wstring text;
static ULONGLONG began=0;
static unsigned speed=12;
static LRESULT CALLBACK procedure(HWND w,UINT msg,WPARAM wp,LPARAM lp){
 if(msg==WM_NCHITTEST)return HTTRANSPARENT;
 if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
 if(msg==WM_ERASEBKGND)return 1;
 if(msg==WM_TIMER){
  HWND game=owner.load();RECT r{};
  if(!visible||!game||GetForegroundWindow()!=game||IsIconic(game)||!GetClientRect(game,&r)){ShowWindow(w,SW_HIDE);return 0;}
  float s=std::min(r.right/1920.f,r.bottom/1080.f);
  POINT p{LONG((r.right-1920*s)/2+480*s),LONG((r.bottom-1080*s)/2+490*s)};
  if(!ClientToScreen(game,&p))return 0;
  SetWindowPos(w,HWND_TOPMOST,p.x,p.y,int(960*s),int(345*s),SWP_NOACTIVATE|SWP_SHOWWINDOW);
  InvalidateRect(w,nullptr,FALSE);return 0;
 }
 if(msg==WM_PAINT){
  PAINTSTRUCT ps;HDC dc=BeginPaint(w,&ps);RECT r{};GetClientRect(w,&r);
  if(r.right>0&&r.bottom>0){
   auto mem=CreateCompatibleDC(dc);auto bitmap=CreateCompatibleBitmap(dc,r.right,r.bottom);auto old=SelectObject(mem,bitmap);
   {
    Gdiplus::Graphics g(mem);g.Clear(Gdiplus::Color(255,255,0,255));g.ScaleTransform(r.right/960.f,r.bottom/345.f);
    g.SetTextRenderingHint(Gdiplus::TextRenderingHintAntiAliasGridFit);
    std::wstring copy;ULONGLONG start;unsigned rate;
    {std::lock_guard<std::mutex> guard(mutex);copy=text;start=began;rate=speed;}
    auto split=copy.find(L'\n');auto heading=copy.substr(0,split);auto body=split==std::wstring::npos?L"":copy.substr(split+1);
    Gdiplus::Font font(L"Arial",25,Gdiplus::FontStyleRegular,Gdiplus::UnitPixel);
    Gdiplus::StringFormat format;format.SetFormatFlags(Gdiplus::StringFormatFlagsLineLimit);
    Gdiplus::RectF measured;g.MeasureString(body.c_str(),-1,&font,Gdiplus::RectF(0,0,958,30000),&format,&measured);
    double offset=noticescroll::pixelOffset(GetTickCount64()-start,measured.Height,297,rate);
    Gdiplus::SolidBrush white(Gdiplus::Color(255,255,255,255));
    float pulse=(sinf(float((GetTickCount64()-start)%4000)*.0015707963f)+1)*.5f;
    Gdiplus::SolidBrush color(Gdiplus::Color(255,BYTE(40+215*pulse),255,0));
    g.DrawString(heading.c_str(),-1,&font,Gdiplus::RectF(0,0,958,42),&format,&color);
    g.SetClip(Gdiplus::RectF(0,44,960,297));
    g.DrawString(body.c_str(),-1,&font,Gdiplus::RectF(0,44-float(offset),958,30000),&format,&white);
   }
   BitBlt(dc,0,0,r.right,r.bottom,mem,0,0,SRCCOPY);SelectObject(mem,old);DeleteObject(bitmap);DeleteDC(mem);
  }
  EndPaint(w,&ps);return 0;
 }
 return DefWindowProcW(w,msg,wp,lp);
}
static DWORD WINAPI run(void*){
 ULONG_PTR token=0;Gdiplus::GdiplusStartupInput input;
 if(Gdiplus::GdiplusStartup(&token,&input,nullptr)!=Gdiplus::Ok){started=false;return 1;}
 WNDCLASSW c{};c.lpfnWndProc=procedure;c.hInstance=self;c.lpszClassName=L"REDELBE_SmoothNotice";
 RegisterClassW(&c);
 auto w=CreateWindowExW(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW|WS_EX_LAYERED|WS_EX_TRANSPARENT,c.lpszClassName,L"REDELBE Notice",WS_POPUP,0,0,960,345,owner.load(),nullptr,self,nullptr);
 if(w){SetLayeredWindowAttributes(w,RGB(255,0,255),255,LWA_COLORKEY);SetTimer(w,1,16,nullptr);updatenotice::smoothReady=true;
  MSG m;while(GetMessageW(&m,nullptr,0,0)>0){TranslateMessage(&m);DispatchMessageW(&m);}DestroyWindow(w);}
 updatenotice::smoothReady=false;started=false;Gdiplus::GdiplusShutdown(token);return 0;
}
static void sync(){
 visible=updatenotice::inWindow&&!updatenotice::developerPage&&updatenotice::scrollEnabled;
 if(!visible)return;
 auto game=GetForegroundWindow();DWORD pid=0;GetWindowThreadProcessId(game,&pid);if(pid!=GetCurrentProcessId())return;
 {std::lock_guard<std::mutex> guard(mutex);if(began!=updatenotice::scrollStarted){text=updatenotice::plainNotice;began=updatenotice::scrollStarted;speed=std::max(1u,std::min(60u,GetPrivateProfileIntW(L"UpdateInfo",L"ScrollPixelsPerSecond",12,(gameRoot+L"REDELBE_LR\\update_info.ini").c_str())));}}
 owner=game;if(!started.exchange(true)){auto t=CreateThread(nullptr,0,run,nullptr,0,nullptr);if(t)CloseHandle(t);else started=false;}
}
}

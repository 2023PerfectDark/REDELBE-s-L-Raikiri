#pragma once
#include <objidl.h>
#include <gdiplus.h>
#pragma comment(lib,"gdiplus.lib")
namespace birthdays { namespace display {
static std::atomic<bool> visible{false},started{false};
static std::atomic<HWND> owner{nullptr};
static HFONT font=nullptr;
static Gdiplus::Image* banner=nullptr;
static LRESULT CALLBACK procedure(HWND window,UINT msg,WPARAM wp,LPARAM lp){
    if(msg==WM_NCHITTEST)return HTTRANSPARENT;
    if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
    if(msg==WM_ERASEBKGND)return 1;
    if(msg==WM_TIMER){
        auto game=owner.load();RECT r{};
        if(!visible||!game||GetForegroundWindow()!=game||IsIconic(game)||!GetClientRect(game,&r)){ShowWindow(window,SW_HIDE);return 0;}
        float s=std::min(r.right/1920.f,r.bottom/1080.f);if(s<=0)return 0;
        int width=banner?1024:1200,height=banner?334:130;
        POINT p{LONG((r.right-width*s)/2),LONG((r.bottom-1080*s)/2+(banner?130:290)*s)};
        if(!ClientToScreen(game,&p))return 0;
        RECT current{};GetWindowRect(window,&current);
        int w=int(width*s),h=int(height*s);
        if(!IsWindowVisible(window)||current.left!=p.x||current.top!=p.y||current.right-current.left!=w||current.bottom-current.top!=h){
            SetWindowPos(window,HWND_TOPMOST,p.x,p.y,w,h,SWP_NOACTIVATE|SWP_SHOWWINDOW);
            InvalidateRect(window,nullptr,FALSE);
        }
        return 0;
    }
    if(msg==WM_PAINT){
        PAINTSTRUCT ps;auto dc=BeginPaint(window,&ps);RECT r{};GetClientRect(window,&r);
        if(banner){
            auto memory=CreateCompatibleDC(dc);auto bitmap=CreateCompatibleBitmap(dc,r.right,r.bottom);auto previous=SelectObject(memory,bitmap);
            {
                Gdiplus::Graphics graphics(memory);graphics.Clear(Gdiplus::Color(255,0,0,0));
                graphics.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
                float sourceWidth=float(banner->GetWidth()),sourceHeight=sourceWidth*r.bottom/r.right;
                float sourceY=std::max(0.f,(float(banner->GetHeight())-sourceHeight)*.30f);
                graphics.DrawImage(banner,Gdiplus::Rect(0,0,r.right,r.bottom),0.f,sourceY,sourceWidth,sourceHeight,Gdiplus::UnitPixel);
            }
            BitBlt(dc,0,0,r.right,r.bottom,memory,0,0,SRCCOPY);
            SelectObject(memory,previous);DeleteObject(bitmap);DeleteDC(memory);EndPaint(window,&ps);return 0;
        }
        SetMapMode(dc,MM_ANISOTROPIC);SetWindowExtEx(dc,1200,130,nullptr);SetViewportExtEx(dc,r.right,r.bottom,nullptr);
        RECT area{0,0,1200,130};auto brush=CreateSolidBrush(RGB(255,0,255));FillRect(dc,&area,brush);DeleteObject(brush);
        auto old=SelectObject(dc,font);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(255,225,45));
        DrawTextW(dc,heading.c_str(),-1,&area,DT_CENTER|DT_VCENTER|DT_WORDBREAK|DT_NOPREFIX);
        SelectObject(dc,old);EndPaint(window,&ps);return 0;
    }
    return DefWindowProcW(window,msg,wp,lp);
}
static DWORD WINAPI run(void*){
    ULONG_PTR token=0;Gdiplus::GdiplusStartupInput startup;
    if(!bannerFile.empty()&&Gdiplus::GdiplusStartup(&token,&startup,nullptr)==Gdiplus::Ok){
        banner=Gdiplus::Image::FromFile((gameRoot+L"REDELBE_LR/BirthdayMessages/"+bannerFile).c_str());
        if(!banner||banner->GetLastStatus()!=Gdiplus::Ok){delete banner;banner=nullptr;log("BIRTHDAY image unavailable; text fallback");}
        else log("BIRTHDAY image loaded "+utf8(bannerFile));
    }
    WNDCLASSW c{};c.lpfnWndProc=procedure;c.hInstance=self;c.lpszClassName=L"REDELBE_BirthdayHeading";
    if(!RegisterClassW(&c)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS){started=false;return 1;}
    font=CreateFontW(-58,0,0,0,FW_BOLD,TRUE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,DEFAULT_PITCH,L"Arial");
    auto window=CreateWindowExW(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW|WS_EX_LAYERED|WS_EX_TRANSPARENT,c.lpszClassName,L"Birthday",WS_POPUP,0,0,1200,130,owner.load(),nullptr,self,nullptr);
    if(!window){DeleteObject(font);started=false;return 1;}
    SetLayeredWindowAttributes(window,RGB(255,0,255),255,banner?LWA_ALPHA:LWA_COLORKEY);SetTimer(window,1,50,nullptr);
    MSG m;while(GetMessageW(&m,nullptr,0,0)>0){TranslateMessage(&m);DispatchMessageW(&m);}
    DestroyWindow(window);DeleteObject(font);delete banner;banner=nullptr;if(token)Gdiplus::GdiplusShutdown(token);started=false;return 0;
}
static void sync(){
    visible=!heading.empty()&&updatenotice::inWindow&&!updatenotice::developerPage;
    if(!visible)return;
    auto game=GetForegroundWindow();DWORD pid=0;GetWindowThreadProcessId(game,&pid);if(pid!=GetCurrentProcessId())return;
    owner=game;if(!started.exchange(true)){auto thread=CreateThread(nullptr,0,run,nullptr,0,nullptr);if(thread)CloseHandle(thread);else started=false;}
}
}}


#pragma once
#pragma comment(lib,"gdi32.lib")
#pragma comment(lib,"msimg32.lib")
#include "ticket_icon.h"
namespace tickets { namespace display {
static std::atomic<bool> visible{false},started{false};
static std::atomic<HWND> owner{nullptr};
static HFONT font=nullptr;
static std::atomic<bool> rewardMode{false};

static LRESULT CALLBACK procedure(HWND window,UINT message,WPARAM wp,LPARAM lp){
    if(message==WM_NCHITTEST)return HTTRANSPARENT;
    if(message==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
    if(message==WM_ERASEBKGND)return 1;
    if(message==WM_TIMER){
        HWND game=owner.load();RECT rect{};
        if(!visible||(rewardMode&&GetTickCount64()>=rewardUntil.load())||!game||GetForegroundWindow()!=game||IsIconic(game)||!GetClientRect(game,&rect)){
            ShowWindow(window,SW_HIDE);return 0;
        }
        float scale=std::min(rect.right/1920.f,rect.bottom/1080.f);
        if(scale<=0){ShowWindow(window,SW_HIDE);return 0;}
        POINT point{LONG((rect.right-1920*scale)*.5f+(rewardMode?815:410)*scale),LONG((rect.bottom-1080*scale)*.5f+(rewardMode?900:142)*scale)};
        if(!ClientToScreen(game,&point)){ShowWindow(window,SW_HIDE);return 0;}
        SetWindowPos(window,HWND_TOPMOST,point.x,point.y,int(290*scale),int(40*scale),SWP_NOACTIVATE|SWP_SHOWWINDOW);
        InvalidateRect(window,nullptr,FALSE);return 0;
    }
    if(message==WM_PAINT){
        PAINTSTRUCT paint;HDC dc=BeginPaint(window,&paint);RECT actual{};GetClientRect(window,&actual);
        SetMapMode(dc,MM_ANISOTROPIC);SetWindowExtEx(dc,290,40,nullptr);SetViewportExtEx(dc,actual.right,actual.bottom,nullptr);
        RECT area{0,0,290,40};FillRect(dc,&area,static_cast<HBRUSH>(GetStockObject(BLACK_BRUSH)));
        auto old=SelectObject(dc,font);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(242,207,117));
        if(rewardMode){RECT label{10,0,155,37};SetTextColor(dc,RGB(255,255,255));DrawTextW(dc,L"You won",-1,&label,DT_LEFT|DT_VCENTER|DT_SINGLELINE);}
        drawIcon(dc,rewardMode?155:6,1,38);
        SetTextColor(dc,RGB(255,255,255));RECT value{rewardMode?198:48,0,282,37};auto text=std::to_wstring(rewardMode?rewardAmount.load():balance());
        DrawTextW(dc,text.c_str(),-1,&value,DT_RIGHT|DT_VCENTER|DT_SINGLELINE);
        RECT line{0,38,290,40};FillRect(dc,&line,static_cast<HBRUSH>(GetStockObject(WHITE_BRUSH)));
        SelectObject(dc,old);EndPaint(window,&paint);return 0;
    }
    return DefWindowProcW(window,message,wp,lp);
}
static DWORD WINAPI run(void*){
    WNDCLASSW cls{};cls.lpfnWndProc=procedure;cls.hInstance=self;cls.lpszClassName=L"REDELBE_LocalTicketBalance";
    if(!RegisterClassW(&cls)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS){started=false;return 1;}
    font=CreateFontW(-27,0,0,0,FW_BOLD,TRUE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,DEFAULT_PITCH,L"Arial");
    HWND window=CreateWindowExW(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW|WS_EX_LAYERED|WS_EX_TRANSPARENT,cls.lpszClassName,L"Local Tickets",WS_POPUP,0,0,290,40,owner.load(),nullptr,self,nullptr);
    if(!window){DeleteObject(font);font=nullptr;started=false;return 1;}
    SetLayeredWindowAttributes(window,0,230,LWA_ALPHA);SetTimer(window,1,100,nullptr);
    MSG message;while(GetMessageW(&message,nullptr,0,0)>0){TranslateMessage(&message);DispatchMessageW(&message);}
    DestroyWindow(window);DeleteObject(font);font=nullptr;started=false;return 0;
}
static void sync(bool wardrobe){
    rewardMode=!wardrobe&&GetTickCount64()<rewardUntil.load();
    visible=(wardrobe||rewardMode)&&userconfig::current.flag("Tickets","enabled");
    if(!visible)return;
    HWND game=GetForegroundWindow();DWORD pid=0;GetWindowThreadProcessId(game,&pid);
    if(pid!=GetCurrentProcessId())return;
    owner=game;
    if(!started.exchange(true)){HANDLE thread=CreateThread(nullptr,0,run,nullptr,0,nullptr);if(thread)CloseHandle(thread);else started=false;}
}
}}

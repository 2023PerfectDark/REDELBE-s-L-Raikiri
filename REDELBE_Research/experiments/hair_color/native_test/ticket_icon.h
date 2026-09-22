#pragma once
#include "ticket_icon_data.h"
#pragma comment(lib,"msimg32.lib")
namespace tickets {
static void drawIcon(HDC target,int x,int y,int size){
    // Separate GDI objects per UI thread; never select one bitmap into two DCs.
    struct Image {
        HDC dc=nullptr;HBITMAP bitmap=nullptr;HGDIOBJ previous=nullptr;
        Image(){
            BITMAPINFO info{};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
            info.bmiHeader.biWidth=64;info.bmiHeader.biHeight=-64;
            info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;
            info.bmiHeader.biCompression=BI_RGB;void* pixels=nullptr;
            dc=CreateCompatibleDC(nullptr);
            if(dc)bitmap=CreateDIBSection(dc,&info,DIB_RGB_COLORS,&pixels,nullptr,0);
            if(bitmap&&pixels){memcpy(pixels,ticketIconPixels,sizeof(ticketIconPixels));previous=SelectObject(dc,bitmap);}
        }
        ~Image(){if(previous)SelectObject(dc,previous);if(bitmap)DeleteObject(bitmap);if(dc)DeleteDC(dc);}
    };
    static thread_local Image icon;
    if(icon.dc&&icon.bitmap){BLENDFUNCTION blend{AC_SRC_OVER,0,255,AC_SRC_ALPHA};AlphaBlend(target,x,y,size,size,icon.dc,0,0,64,64,blend);}
}
}

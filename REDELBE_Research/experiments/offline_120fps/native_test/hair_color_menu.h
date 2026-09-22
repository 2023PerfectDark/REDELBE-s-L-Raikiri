#pragma once
#pragma comment(lib,"gdi32.lib")
// DOA Central research UI. An owned, nonactivating window; not a native KSCL tab.
// Only prevalidated albedo files in the prepared package can be selected.
namespace haircolor {
static const wchar_t* names[]={L"Default",L"Blonde",L"Red",L"Blue",L"Silver",L"Pink",L"Black"};
static std::map<uint32_t,std::vector<std::pair<std::wstring,std::wstring>>> resources;
static std::atomic<bool> visible{false};
static std::atomic<int> pending{-1},current{0};
static std::atomic<bool> expanded{false};
static std::atomic<int> focus{0};
static std::atomic<HWND> gameWindow{nullptr},window{nullptr};
static std::atomic<uint32_t> activeHair{0};
static HFONT font=nullptr;
static uint32_t currentCharacter=0,currentHair=0;
static unsigned currentSlot=0;
static bool context=false,started=false;
static bool refresh=false;
static std::wstring settings;
static LRESULT CALLBACK proc(HWND w,UINT msg,WPARAM wp,LPARAM lp){
 if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
 if(msg==WM_RBUTTONUP){expanded=false;return 0;}
 if(msg==WM_LBUTTONUP){if(!expanded){focus=current.load();expanded=true;return 0;}RECT r;GetClientRect(w,&r);int y=static_cast<short>(HIWORD(lp))*540/std::max(1l,r.bottom);int index=(y-65)/58;if(y>=65&&index>=0&&index<7){focus=index;pending=index;}else if(y>=490)expanded=false;return 0;}
 if(msg==WM_ERASEBKGND)return 1;
 if(msg==WM_PAINT){PAINTSTRUCT ps;auto dc=BeginPaint(w,&ps);RECT physical;GetClientRect(w,&physical);SetMapMode(dc,MM_ANISOTROPIC);SetWindowExtEx(dc,630,expanded?540:50,nullptr);SetViewportExtEx(dc,physical.right,physical.bottom,nullptr);RECT r{0,0,630,expanded?540:50};auto brush=CreateSolidBrush(RGB(22,22,24));FillRect(dc,&r,brush);DeleteObject(brush);SelectObject(dc,font);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(255,255,255));RECT title{16,3,614,50};std::wstring label=expanded?L"HAIR COLOR":std::wstring(L"Hair Color: ")+names[current]+L"     [Y / H]";DrawTextW(dc,label.c_str(),-1,&title,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
  if(expanded){for(int i=0;i<7;i++){RECT row{8,65+i*58,622,121+i*58};if(i==focus){auto b=CreateSolidBrush(RGB(234,107,15));FillRect(dc,&row,b);DeleteObject(b);}row.left+=16;std::wstring text=names[i];if(i==current)text+=L"  *";DrawTextW(dc,text.c_str(),-1,&row,DT_LEFT|DT_VCENTER|DT_SINGLELINE);}RECT back{20,490,612,534};DrawTextW(dc,L"A / Click: Apply     B / Right-click: Back",-1,&back,DT_LEFT|DT_VCENTER|DT_SINGLELINE);}EndPaint(w,&ps);return 0;}
 if(msg==WM_TIMER){auto owner=gameWindow.load();bool show=visible&&owner&&GetForegroundWindow()==owner&&!IsIconic(owner);if(!show){ShowWindow(w,SW_HIDE);return 0;}RECT r{};GetClientRect(owner,&r);float scale=std::min(r.right/1920.f,r.bottom/1080.f);POINT p{LONG((r.right-1920*scale)/2+95*scale),LONG((r.bottom-1080*scale)/2+(expanded?365:855)*scale)};ClientToScreen(owner,&p);SetWindowPos(w,HWND_TOPMOST,p.x,p.y,int(630*scale),int((expanded?540:50)*scale),SWP_NOACTIVATE|SWP_SHOWWINDOW);InvalidateRect(w,nullptr,FALSE);return 0;}
 return DefWindowProcW(w,msg,wp,lp);
}
static DWORD WINAPI thread(void*){
 WNDCLASSW c{};c.lpfnWndProc=proc;c.hInstance=self;c.lpszClassName=L"REDELBE_LR_HairColorResearch";c.hCursor=LoadCursor(nullptr,IDC_ARROW);if(!RegisterClassW(&c)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS)return 1;
 font=CreateFontW(-23,0,0,0,FW_SEMIBOLD,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Arial");
 HWND w=CreateWindowExW(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,c.lpszClassName,L"Hair Color",WS_POPUP,0,0,320,310,gameWindow,nullptr,self,nullptr);window=w;if(!w)return 1;SetTimer(w,1,100,nullptr);MSG msg;while(GetMessageW(&msg,nullptr,0,0)>0){TranslateMessage(&msg);DispatchMessageW(&msg);}return 0;
}
static void initialize(){
 // The native get_my_character_custom_slot reports the main-fighter slot,
 // not the slot currently being edited. Use the observed slot cursor events.
 std::ifstream f(workRoot+L"hair_colors.tsv");std::string line;
 while(std::getline(f,line)){std::istringstream s(line);std::string hair,id,label;if(!std::getline(s,hair,'\t')||!std::getline(s,id,'\t'))continue;if(hair.size()!=8||id.size()!=8)continue;try{auto h=static_cast<uint32_t>(std::stoul(hair,nullptr,16));auto source=full((gameRoot+L"fdata_package\\data\\0x"+wide(id)+L".file").c_str());auto prefix=workRoot+L"HairColors\\"+wide(id)+L"_";bool valid=true;for(int i=1;i<7;i++)if(GetFileAttributesW((prefix+names[i]+L".file").c_str())==INVALID_FILE_ATTRIBUTES)valid=false;if(valid)resources[h].push_back({source,prefix});}catch(...){} }
 settings=gameRoot+L"REDELBE_LR\\HairColors.prototype.ini";
}
static bool pointerOver(){auto w=window.load();if(!w||!IsWindowVisible(w))return false;POINT p;RECT r;return GetCursorPos(&p)&&GetWindowRect(w,&r)&&PtInRect(&r,p);}
static std::wstring key(uint32_t chara,unsigned slot){return wide(hex(chara))+L"_slot_"+std::to_wstring(slot);}
static void sync(bool show,uint32_t hair,uint32_t chara,unsigned slot){
 bool previousContext=context;context=show&&resources.count(hair)!=0;activeHair=context?hair:0;visible=context;if(!context)expanded=false;
 if(!context)return;
 if(currentCharacter!=chara||currentSlot!=slot||currentHair!=hair){int old=current;currentCharacter=chara;currentSlot=slot;currentHair=hair;unsigned saved=GetPrivateProfileIntW(L"Colors",key(chara,slot).c_str(),0,settings.c_str());current=saved<=6?saved:0;pending=-1;focus=current.load();if(old||current)refresh=true;}
 if(!previousContext&&current)refresh=true;
 DWORD pid=0;auto w=GetForegroundWindow();GetWindowThreadProcessId(w,&pid);if(pid==GetCurrentProcessId()&&w!=window){gameWindow=w;if(!started){started=true;auto t=CreateThread(nullptr,0,thread,nullptr,0,nullptr);if(t)CloseHandle(t);}}
}
static std::wstring select(const std::wstring& path){
 if(!visible||!current)return L"";
 auto it=resources.find(activeHair);if(it==resources.end())return L"";
 for(auto& entry:it->second)if(entry.first==path)return entry.second+names[current]+L".file";
 return L"";
}
static bool take(){if(refresh&&context){refresh=false;return true;}int value=pending.exchange(-1);if(!context||value<0||value>6||value==current)return false;current=value;WritePrivateProfileStringW(L"Colors",key(currentCharacter,currentSlot).c_str(),std::to_wstring(value).c_str(),settings.c_str());return true;}
static void pad(DWORD player,XINPUT_STATE* state,DWORD result){
 static WORD previous[4]{},swallowed[4]{};if(player>=4||result!=ERROR_SUCCESS)return;WORD buttons=state->Gamepad.wButtons,edge=buttons&~previous[player];previous[player]=buttons;swallowed[player]&=buttons;
 state->Gamepad.wButtons&=~swallowed[player];if(player!=0||!visible)return;bool block=expanded;
 if(edge&XINPUT_GAMEPAD_Y){expanded=!expanded;focus=current.load();block=true;}
 if(expanded){if(edge&XINPUT_GAMEPAD_DPAD_UP)focus=(focus.load()+6)%7;if(edge&XINPUT_GAMEPAD_DPAD_DOWN)focus=(focus.load()+1)%7;if(edge&XINPUT_GAMEPAD_A)pending=focus.load();if(edge&XINPUT_GAMEPAD_B)expanded=false;block=true;}
 if(block){swallowed[player]|=buttons;state->Gamepad.wButtons=0;state->Gamepad.sThumbLX=state->Gamepad.sThumbLY=0;state->Gamepad.bLeftTrigger=state->Gamepad.bRightTrigger=0;}
}
static void keyboard(unsigned char* keys){
 static unsigned char swallowed[256]{};
 static bool oldH=false,oldUp=false,oldDown=false,oldA=false,oldB=false;
 bool h=(keys[0x23]&0x80)!=0,up=(keys[0xc8]&0x80)!=0,down=(keys[0xd0]&0x80)!=0,a=(keys[0x1c]&0x80)!=0,b=(keys[1]&0x80)!=0;
 for(int i=0;i<256;i++){swallowed[i]&=keys[i];keys[i]&=~swallowed[i];}
 if(visible){bool block=expanded;if(h&&!oldH){expanded=!expanded;focus=current.load();block=true;}if(expanded){if(up&&!oldUp)focus=(focus.load()+6)%7;if(down&&!oldDown)focus=(focus.load()+1)%7;if(a&&!oldA)pending=focus.load();if(b&&!oldB)expanded=false;block=true;}if(block){for(int i=0;i<256;i++)swallowed[i]|=keys[i];memset(keys,0,256);}else keys[0x23]=0;}
 oldH=h;oldUp=up;oldDown=down;oldA=a;oldB=b;
}
}

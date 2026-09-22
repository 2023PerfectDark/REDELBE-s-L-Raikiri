// Included inside animationpreviewtest. This owns no game resource pointers.
struct Entry {std::string character,category,name;std::wstring path;};
static std::vector<Entry> entries;
static std::vector<std::string> characters;
static std::vector<size_t> filtered;
static std::wstring libraryRoot;
static size_t characterIndex=0,page=0,cursor=0;
static bool victoryOnly=true;
static int chosen=-1;
static std::wstring status=L"Select the same character in Wardrobe and in this list.";
static std::atomic<HWND> owner{},browserWindow{};
static std::atomic<bool> uiStarted{},confirmation{};
static std::atomic<bool> confirmYes{};
static std::atomic<int> command{};
static HFONT browserFont{};
static void filter(){filtered.clear();page=0;cursor=0;for(size_t i=0;i<entries.size();++i)if((entries[i].character==characters[characterIndex]||entries[i].character=="ALL")&&(!victoryOnly||entries[i].category=="Victory"))filtered.push_back(i);}
static void pausePlayback(){auto clip=std::atomic_load(&selected);if(!clip)return;if(!paused){position=static_cast<float>(std::fmod(position.load()+(GetTickCount64()-started.load())/1000.,clip->seconds));paused=true;}else{started=GetTickCount64();paused=false;}}
static void choose(size_t row){if(row>=filtered.size())return;active=false;chosen=int(filtered[row]);auto& e=entries[chosen];camera::select(libraryRoot,e.name,characters[characterIndex]);if(loadClip(e.path)){auto leaf=e.path.substr(e.path.find_last_of(L"/\\")+1);if(characters[characterIndex]=="KAS"&&loadClip(libraryRoot+L"Faces\\"+leaf,true))log("ANIMATION BROWSER facial companion ready "+e.name);active=true;status=L"Playing: "+std::wstring(e.name.begin(),e.name.end());log("ANIMATION BROWSER selected "+e.name);}else{status=L"This clip failed validation. Original animation retained.";chosen=-1;}}
static void action(int id){
 if(confirmation){
  if(id==10||id==11||id==4||id==5){confirmYes=!confirmYes;return;}
  if(id==20||(id==12&&confirmYes)){confirmation=false;active=false;return;}
  if(id==9||id==21||id==12){confirmation=false;expanded=false;active=false;return;}
  return;
 }

 if(id==1||id==2){if(characters.empty())return;characterIndex=(characterIndex+characters.size()+(id==1?-1:1))%characters.size();filter();}
 else if(id==3){victoryOnly=!victoryOnly;filter();}
 else if(id==4){if(page)page--;}
 else if(id==5){if((page+1)*12<filtered.size())page++;}
 else if(id==6)pausePlayback();
 else if(id==7){position=0;started=GetTickCount64();paused=false;active=bool(std::atomic_load(&selected));}
 else if(id==8){active=false;paused=false;status=L"Stopped. Native Wardrobe animation restored.";}
 else if(id==9){active=false;expanded=false;}
 else if(id==10||id==11){if(filtered.empty())return;cursor=(cursor+filtered.size()+(id==10?-1:1))%filtered.size();page=cursor/12;}
 else if(id==12)choose(cursor);
 else if(id==13){camera::controls=!camera::controls;camera::reset=true;}
 else if(id>=100&&id<112){cursor=page*12+id-100;choose(cursor);}
}
static void label(HDC dc,int x,int y,int width,int height,const std::wstring& text,bool button=false){RECT r{x,y,x+width,y+height};if(button){auto b=CreateSolidBrush(RGB(65,65,72));FillRect(dc,&r,b);DeleteObject(b);}r.left+=7;DrawTextW(dc,text.c_str(),-1,&r,DT_SINGLELINE|DT_VCENTER|DT_END_ELLIPSIS);}
static LRESULT CALLBACK browserProc(HWND w,UINT msg,WPARAM wp,LPARAM lp){
 if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
 if(msg==WM_RBUTTONUP){action(9);return 0;}
 if(msg==WM_MOUSEWHEEL){if(confirmation)return 0;if(camera::controls){camera::zoom=camera::zoom.load()+(GET_WHEEL_DELTA_WPARAM(wp)>0?-.025f:.025f);return 0;}action(GET_WHEEL_DELTA_WPARAM(wp)>0?4:5);return 0;}
 if(msg==WM_LBUTTONUP){RECT r{};GetClientRect(w,&r);int x=short(LOWORD(lp))*700/std::max(1l,r.right),y=short(HIWORD(lp))*680/std::max(1l,r.bottom);if(confirmation){if(y>=260&&y<310)action(x<350?20:21);return 0;}if(y>=48&&y<86){if(x<60)action(1);else if(x<330)action(2);else action(3);}else if(y>=100&&y<520)action(100+(y-100)/35);else if(y>=530&&y<568)action(x<350?4:5);else if(y>=580&&y<620)action(6+std::min(3,std::max(0,x/175)));else if(y>=650)action(13);return 0;}
 if(msg==WM_ERASEBKGND)return 1;
 if(msg==WM_PAINT){PAINTSTRUCT ps;auto dc=BeginPaint(w,&ps);RECT r{};GetClientRect(w,&r);auto mem=CreateCompatibleDC(dc);auto bitmap=CreateCompatibleBitmap(dc,r.right,r.bottom);auto old=SelectObject(mem,bitmap);SetMapMode(mem,MM_ANISOTROPIC);SetWindowExtEx(mem,700,680,nullptr);SetViewportExtEx(mem,r.right,r.bottom,nullptr);RECT canvas{0,0,700,680};auto bg=CreateSolidBrush(RGB(20,20,25));FillRect(mem,&canvas,bg);DeleteObject(bg);SelectObject(mem,browserFont);SetBkMode(mem,TRANSPARENT);SetTextColor(mem,RGB(245,245,245));
  if(confirmation){
   label(mem,30,90,640,45,L"Enter Animation Browser?");
   label(mem,30,150,640,35,L"Preview character animations in the current scene.");
   label(mem,30,190,640,35,L"Do you wish to continue?");
   SetTextColor(mem,confirmYes?RGB(255,176,65):RGB(245,245,245));
   label(mem,30,260,310,50,L"Yes, continue",true);
   SetTextColor(mem,!confirmYes?RGB(255,176,65):RGB(245,245,245));
   label(mem,360,260,310,50,L"No, return",true);
   SetTextColor(mem,RGB(245,245,245));
   label(mem,30,340,640,35,L"A / Enter: selected choice     B / Esc: cancel");
  }else{
  label(mem,10,5,680,35,L"ANIMATION BROWSER  /  F8 to close");
  label(mem,10,48,45,38,L"<",true);std::wstring ch=characters.empty()?L"No catalog":std::wstring(characters[characterIndex].begin(),characters[characterIndex].end());label(mem,60,48,265,38,ch+L"    >",true);label(mem,335,48,355,38,victoryOnly?L"Victory clips  /  click for all":L"All body motions  /  click for victory",true);
  for(int row=0;row<12;++row){size_t n=page*12+row;if(n>=filtered.size())break;auto& e=entries[filtered[n]];if(n==cursor){RECT focus{10,100+row*35,690,134+row*35};auto brush=CreateSolidBrush(RGB(42,48,60));FillRect(mem,&focus,brush);DeleteObject(brush);}if(int(filtered[n])==chosen)SetTextColor(mem,RGB(255,176,65));label(mem,10,100+row*35,680,34,std::wstring(e.name.begin(),e.name.end()));SetTextColor(mem,RGB(245,245,245));}
  label(mem,10,530,335,38,L"< Previous page",true);label(mem,355,530,335,38,L"Next page >    "+std::to_wstring(filtered.size())+L" clips",true);
  label(mem,10,580,160,40,paused?L"Resume":L"Pause",true);label(mem,180,580,160,40,L"Replay",true);label(mem,355,580,160,40,L"Stop",true);label(mem,530,580,160,40,L"Close",true);
  std::wstring line=status;if(active&&GetTickCount64()-started.load()>1000&&GetTickCount64()-appliedAt.load()>1000)line=L"Waiting for a compatible body. Select this character in Wardrobe.";label(mem,10,625,680,25,line);label(mem,10,650,680,25,camera::controls?L"CAMERA: LS move; Y+LS dolly; RS orbit; D-pad zoom; LT/RT tilt":L"C / Back: camera controls     Native clip camera when available",true);
  if(camera::controls)label(mem,10,625,680,25,L"C / Back: list | WASD/QE move | arrows orbit | R / RS click reset");
  if(active&&GetTickCount64()-camera::updated.load()>1500)label(mem,10,625,680,25,L"Camera waiting for the character preview camera.");
  }
  SetMapMode(mem,MM_TEXT);BitBlt(dc,0,0,r.right,r.bottom,mem,0,0,SRCCOPY);SelectObject(mem,old);DeleteObject(bitmap);DeleteDC(mem);EndPaint(w,&ps);return 0;
 }
 if(msg==WM_TIMER){auto o=owner.load();auto foreground=GetForegroundWindow();bool show=expanded&&GetTickCount64()<=wardrobeUntil&&o&&(foreground==o||foreground==w)&&!IsIconic(o);if(!show){ShowWindow(w,SW_HIDE);return 0;}if(auto c=command.exchange(0))action(c);RECT r{};GetClientRect(o,&r);float scale=std::min(r.right/1920.f,r.bottom/1080.f);POINT point{LONG((r.right-1920*scale)/2+75*scale),LONG((r.bottom-1080*scale)/2+190*scale)};ClientToScreen(o,&point);SetWindowPos(w,HWND_TOPMOST,point.x,point.y,int(700*scale),int(680*scale),SWP_NOACTIVATE|SWP_SHOWWINDOW);InvalidateRect(w,nullptr,FALSE);return 0;}
 return DefWindowProcW(w,msg,wp,lp);
}
static DWORD WINAPI browserThread(void*){WNDCLASSW c{};c.lpfnWndProc=browserProc;c.hInstance=self;c.lpszClassName=L"REDELBE_LR_AnimationBrowser";c.hCursor=LoadCursor(nullptr,IDC_ARROW);if(!RegisterClassW(&c)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS)return 1;browserFont=CreateFontW(-18,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Arial");auto w=CreateWindowExW(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,c.lpszClassName,L"Animation Browser",WS_POPUP,0,0,700,680,owner,nullptr,self,nullptr);browserWindow=w;if(!w)return 1;SetTimer(w,1,33,nullptr);MSG m{};while(GetMessageW(&m,nullptr,0,0)>0){TranslateMessage(&m);DispatchMessageW(&m);}return 0;}
static void initialize(){libraryRoot=gameRoot+L"REDELBE_LR\\AnimationBrowser\\";std::ifstream in(libraryRoot+L"catalog.tsv");std::string line;while(std::getline(in,line)){std::istringstream stream(line);Entry e;std::string rel;if(!std::getline(stream,e.character,'\t')||!std::getline(stream,e.category,'\t')||!std::getline(stream,e.name,'\t')||!std::getline(stream,rel))continue;if(!rel.empty()&&rel.back()=='\r')rel.pop_back();if(rel.rfind("Clips/0x",0)!=0||rel.find("..")!=std::string::npos||rel.find(':')!=std::string::npos)continue;e.path=libraryRoot+std::wstring(rel.begin(),rel.end());entries.push_back(e);if(e.character!="ALL"&&std::find(characters.begin(),characters.end(),e.character)==characters.end())characters.push_back(e.character);}if(!characters.empty()){auto it=std::find(characters.begin(),characters.end(),"KAS");if(it!=characters.end())characterIndex=it-characters.begin();filter();}log("ANIMATION BROWSER catalog="+std::to_string(entries.size()));}
static void poll(bool wardrobe){if(!enabled)return;DWORD pid=0;auto foreground=GetForegroundWindow();GetWindowThreadProcessId(foreground,&pid);bool focused=pid==GetCurrentProcessId();wardrobeUntil=wardrobe?GetTickCount64()+250:0;if(!wardrobe){active=false;expanded=false;confirmation=false;camera::controls=false;return;}if(!focused)return;if(foreground!=browserWindow)owner=foreground;if(!uiStarted.exchange(true)){auto t=CreateThread(nullptr,0,browserThread,nullptr,0,nullptr);if(t)CloseHandle(t);}static bool previous=false;SHORT key=GetAsyncKeyState(VK_F8);bool down=(key&0x8000)!=0;if((down&&!previous)||(key&1)){active=false;if(expanded){expanded=false;confirmation=false;}else{confirmYes=false;confirmation=true;expanded=true;}}previous=down;if(expanded&&!confirmation&&(GetAsyncKeyState('C')&1))command=13;
 if(expanded&&camera::controls&&!confirmation){static ULONGLONG lastCameraKey=0;auto tick=GetTickCount64();float dt=std::min(.05f,(tick-lastCameraKey)/1000.f);lastCameraKey=tick;auto held=[](int k){return (GetAsyncKeyState(k)&0x8000)?1.f:0.f;};camera::moveX=camera::moveX.load()+(held('D')-held('A'))*dt*120;camera::moveY=camera::moveY.load()+(held('E')-held('Q'))*dt*120;camera::moveZ=camera::moveZ.load()+(held('S')-held('W'))*dt*180;camera::lookX=camera::lookX.load()+(held(VK_LEFT)-held(VK_RIGHT))*dt;camera::lookY=camera::lookY.load()+(held(VK_UP)-held(VK_DOWN))*dt;camera::zoom=camera::zoom.load()+(held(VK_NEXT)-held(VK_PRIOR))*dt*.4f;if(GetAsyncKeyState('R')&1)camera::reset=true;if(GetAsyncKeyState(VK_ESCAPE)&1)command=9;return;}
 if(expanded){for(auto pair:{std::pair<int,int>{VK_UP,10},{VK_DOWN,11},{VK_RETURN,12},{VK_ESCAPE,9},{VK_SPACE,6},{VK_PRIOR,4},{VK_NEXT,5}})if(GetAsyncKeyState(pair.first)&1)command=pair.second;}}

// Consume controller input while the browser is visible. UI actions run on its thread.
static bool pad(DWORD player,XINPUT_STATE* state,DWORD result){
 if(result!=ERROR_SUCCESS||!state||player>=4)return false;
 static WORD previous[4]{};WORD buttons=state->Gamepad.wButtons,edge=buttons&~previous[player];previous[player]=buttons;
 if(!enabled||!expanded||GetTickCount64()>wardrobeUntil)return false;
 DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);if(pid!=GetCurrentProcessId())return false;
 if(!confirmation&&(edge&XINPUT_GAMEPAD_BACK)){command=13;state->Gamepad={};return true;}
 if(!confirmation&&camera::controls){static ULONGLONG lastCameraPad[4]{};auto tick=GetTickCount64();float dt=std::min(.05f,(tick-lastCameraPad[player])/1000.f);lastCameraPad[player]=tick;if(player==0)camera::input(state->Gamepad,dt);if(edge&XINPUT_GAMEPAD_B)command=9;state->Gamepad={};return true;}
 int id=0;if(edge&XINPUT_GAMEPAD_B)id=9;else if(edge&XINPUT_GAMEPAD_A)id=12;else if(edge&XINPUT_GAMEPAD_DPAD_UP)id=10;else if(edge&XINPUT_GAMEPAD_DPAD_DOWN)id=11;else if(edge&XINPUT_GAMEPAD_DPAD_LEFT)id=4;else if(edge&XINPUT_GAMEPAD_DPAD_RIGHT)id=5;else if(edge&XINPUT_GAMEPAD_X)id=6;else if(edge&XINPUT_GAMEPAD_Y)id=7;
 if(id)command=id;state->Gamepad={};return true;
}


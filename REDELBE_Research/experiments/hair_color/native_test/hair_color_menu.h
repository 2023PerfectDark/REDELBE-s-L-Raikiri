#pragma once
#pragma comment(lib,"gdi32.lib")
// DOA Central research UI. An owned, nonactivating window; not a native KSCL tab.
// Only prevalidated albedo files in the prepared package can be selected.
namespace haircolor {
static const wchar_t* names[]={L"Default",L"Black",L"Dark Brown",L"Light Brown",L"Dark Blonde",L"Platinum Blonde",L"Silver",L"White",L"Bright Red",L"Orange",L"Yellow",L"Lime Green",L"Cyan",L"Royal Blue",L"Purple",L"Pink"};
static std::map<uint32_t,std::vector<std::pair<std::wstring,std::wstring>>> resources;
static std::atomic<bool> visible{false};
static std::atomic<int> pending{-1},current{0};
static std::atomic<bool> expanded{false};
static std::atomic<int> focus{0};
static std::atomic<HWND> gameWindow{nullptr},window{nullptr};
static std::atomic<uint32_t> activeHair{0};
static HFONT font=nullptr,promptFont=nullptr;
static std::atomic<uint64_t> hoverPosition{~uint64_t(0)};
static uint64_t mousePosition(){POINT p{};if(!GetCursorPos(&p))return ~uint64_t(0);return (uint64_t(uint32_t(p.x))<<32)|uint32_t(p.y);}
static uint32_t currentCharacter=0,currentHair=0;
static unsigned currentSlot=0;
static bool context=false,started=false;
static std::atomic<bool> gDown{false};
static bool pollG(){bool down=(GetAsyncKeyState('G')&0x8000)!=0;bool wasDown=gDown.exchange(down);bool edge=down&&!wasDown;if(visible&&edge){expanded=!expanded;focus=current.load();return true;}return false;}
static bool refresh=false;
static std::wstring settings;
struct PlayerColor {uint32_t character=0,hair=0;unsigned slot=0;int color=0;bool known=false;};
static PlayerColor players[2];
static bool battleHair[2]{};
// During battle all prepared hair resources for the selected character inherit
// the selected hairstyle's color, including damage variants preloaded by LR.
// These routes never modify a different hairstyle's persisted wardrobe choice.
static std::map<uint32_t,std::vector<uint32_t>> battleHairRoutes;
static void beginBattleHair(uint32_t hair){
 for(unsigned side=0;side<2;++side)if(players[side].hair==hair){battleHair[side]=true;}
}
struct SlotRead {uint32_t character=0,hair=0;unsigned slot=0;ULONGLONG at=0;};
static thread_local SlotRead slotRead;
using HairSlotFn=uint32_t(*)(uint32_t,unsigned);
static HairSlotFn hairSlotOriginal=nullptr;
static uint32_t hairSlotHook(uint32_t chara,unsigned slot){
 auto hair=hairSlotOriginal(chara,slot);
 if(chara&&hair&&slot<20)slotRead={chara,hair,slot,GetTickCount64()};
 return hair;
}
static LRESULT CALLBACK proc(HWND w,UINT msg,WPARAM wp,LPARAM lp){
 if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
 if(msg==WM_RBUTTONUP){expanded=false;return 0;}
 if(msg==WM_LBUTTONUP){if(!expanded){focus=current.load();expanded=true;return 0;}RECT r;GetClientRect(w,&r);int y=static_cast<short>(HIWORD(lp))*540/std::max(1l,r.bottom);int x=static_cast<short>(LOWORD(lp))*630/std::max(1l,r.right);int index=((y-65)/100)*4+(x-8)/154;if(y>=65&&y<465&&x>=8&&x<624&&index>=0&&index<16){focus=index;pending=index;}else if(y>=490)expanded=false;return 0;}
 if(msg==WM_MOUSEMOVE&&expanded){auto position=mousePosition();if(hoverPosition.exchange(position)==position)return 0;RECT r;GetClientRect(w,&r);int x=static_cast<short>(LOWORD(lp))*630/std::max(1l,r.right),y=static_cast<short>(HIWORD(lp))*540/std::max(1l,r.bottom);if(x>=8&&x<624&&y>=65&&y<465)focus=((y-65)/100)*4+(x-8)/154;return 0;}
 if(msg==WM_MOUSEWHEEL&&expanded){focus=(focus.load()+(GET_WHEEL_DELTA_WPARAM(wp)>0?12:4))%16;return 0;}
 if(msg==WM_ERASEBKGND)return 1;
 if(msg==WM_PAINT){PAINTSTRUCT ps;auto dc=BeginPaint(w,&ps);RECT physical;GetClientRect(w,&physical);SetMapMode(dc,MM_ANISOTROPIC);SetWindowExtEx(dc,expanded?630:400,expanded?540:50,nullptr);SetViewportExtEx(dc,physical.right,physical.bottom,nullptr);RECT r{0,0,630,expanded?540:50};auto brush=CreateSolidBrush(expanded?RGB(22,22,24):RGB(255,0,255));FillRect(dc,&r,brush);DeleteObject(brush);SelectObject(dc,expanded?font:promptFont);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(255,255,255));RECT title{16,3,614,50};std::wstring label=expanded?L"HAIR COLOR":L"Change Hair Color";
  if(!expanded){
   // Vector controller glyphs stay crisp at any resolution. DualSense uses a
   // monochrome Square; Xbox uses the blue X face button.
   auto pen=CreatePen(PS_SOLID,2,RGB(220,220,220));auto oldPen=SelectObject(dc,pen);auto oldBrush=SelectObject(dc,GetStockObject(BLACK_BRUSH));
   Ellipse(dc,4,11,32,39);Rectangle(dc,12,19,24,31);
   Ellipse(dc,42,11,70,39);SetTextColor(dc,RGB(80,165,255));RECT xbox{42,10,70,39};DrawTextW(dc,L"X",1,&xbox,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
   SetTextColor(dc,RGB(255,255,255));RoundRect(dc,81,12,109,38,4,4);RECT key{81,10,109,39};DrawTextW(dc,L"G",1,&key,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
   SelectObject(dc,oldBrush);SelectObject(dc,oldPen);DeleteObject(pen);title.left=119;title.right=400;
  }
  DrawTextW(dc,label.c_str(),-1,&title,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
  if(expanded){
   tickets::drawIcon(dc,465,9,30);RECT balanceRect{502,3,614,50};auto balanceText=std::to_wstring(tickets::balance());DrawTextW(dc,balanceText.c_str(),-1,&balanceRect,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
   for(int i=0;i<16;i++){
    int col=i%4,line=i/4;RECT row{8+col*154,65+line*100,160+col*154,163+line*100};
    if(i==focus){auto b=CreateSolidBrush(RGB(234,107,15));FillRect(dc,&row,b);DeleteObject(b);}
    row.left+=6;row.right-=6;
    bool locked=i&&tickets::gated()&&!tickets::owned(currentCharacter,currentHair,i);
    std::wstring text=names[i];if(locked)text+=L":";if(i==current)text+=L" *";
    SIZE measured{};GetTextExtentPoint32W(dc,text.c_str(),int(text.size()),&measured);
    if(locked){
     auto price=std::to_wstring(userconfig::current.number("Tickets","hair_color_cost"));SIZE priceSize{};GetTextExtentPoint32W(dc,price.c_str(),int(price.size()),&priceSize);
     bool inlinePrice=measured.cx+32+priceSize.cx<=row.right-row.left;
     RECT nameRect=row;nameRect.top+=inlinePrice?32:10;nameRect.bottom=nameRect.top+30;
     DrawTextW(dc,text.c_str(),-1,&nameRect,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
     int px=inlinePrice?row.left+measured.cx+3:row.left;int py=inlinePrice?row.top+32:row.top+48;
     tickets::drawIcon(dc,px,py,26);RECT costRect{px+29,py,row.right,py+30};DrawTextW(dc,price.c_str(),-1,&costRect,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
    }else DrawTextW(dc,text.c_str(),-1,&row,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
   }
   RECT back{20,490,612,534};DrawTextW(dc,L"A / Click: Apply     B / Right-click: Back",-1,&back,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
  }EndPaint(w,&ps);return 0;}
 if(msg==WM_TIMER){auto owner=gameWindow.load();bool show=visible&&owner&&GetForegroundWindow()==owner&&!IsIconic(owner);if(!show){ShowWindow(w,SW_HIDE);return 0;}RECT r{};GetClientRect(owner,&r);float scale=std::min(r.right/1920.f,r.bottom/1080.f);POINT p{LONG((r.right-1920*scale)/2+(expanded?95:760)*scale),LONG((r.bottom-1080*scale)/2+(expanded?365:995)*scale)};ClientToScreen(owner,&p);RECT oldRect{};GetWindowRect(w,&oldRect);int width=int((expanded?630:400)*scale),height=int((expanded?540:50)*scale);if(!IsWindowVisible(w)||oldRect.left!=p.x||oldRect.top!=p.y||oldRect.right-oldRect.left!=width||oldRect.bottom-oldRect.top!=height)SetWindowPos(w,HWND_TOPMOST,p.x,p.y,width,height,SWP_NOACTIVATE|SWP_SHOWWINDOW);InvalidateRect(w,nullptr,FALSE);return 0;}
 return DefWindowProcW(w,msg,wp,lp);
}
static DWORD WINAPI thread(void*){
 WNDCLASSW c{};c.lpfnWndProc=proc;c.hInstance=self;c.lpszClassName=L"REDELBE_LR_HairColorResearch";c.hCursor=LoadCursor(nullptr,IDC_ARROW);if(!RegisterClassW(&c)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS)return 1;
 font=CreateFontW(-18,0,0,0,FW_SEMIBOLD,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Arial");
 promptFont=CreateFontW(-24,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,DEFAULT_PITCH,L"Arial");
 HWND w=CreateWindowExW(WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW|WS_EX_LAYERED,c.lpszClassName,L"Hair Color",WS_POPUP,0,0,320,310,gameWindow,nullptr,self,nullptr);window=w;if(!w)return 1;SetLayeredWindowAttributes(w,RGB(255,0,255),255,LWA_COLORKEY);SetTimer(w,1,16,nullptr);MSG msg;while(GetMessageW(&msg,nullptr,0,0)>0){TranslateMessage(&msg);DispatchMessageW(&msg);}return 0;
}
static void initialize(){
 // The native get_my_character_custom_slot reports the main-fighter slot,
 // not the slot currently being edited. Use the observed slot cursor events.
 auto paletteRoot=gameRoot+L"REDELBE_LR\\HairColorSupport\\";
 if(GetFileAttributesW((paletteRoot+L"hair_colors.tsv").c_str())==INVALID_FILE_ATTRIBUTES)paletteRoot=workRoot;
 std::ifstream f(paletteRoot+L"hair_colors.tsv");std::string line;
 while(std::getline(f,line)){std::istringstream s(line);std::string hair,id,label;if(!std::getline(s,hair,'\t')||!std::getline(s,id,'\t'))continue;if(hair.size()!=8||id.size()!=8)continue;try{auto h=static_cast<uint32_t>(std::stoul(hair,nullptr,16));auto source=full((gameRoot+L"fdata_package\\data\\0x"+wide(id)+L".file").c_str());auto prefix=paletteRoot+L"HairColors\\"+wide(id)+L"_";bool valid=true;for(int i=1;i<16;i++)if(GetFileAttributesW((prefix+names[i]+L".file").c_str())==INVALID_FILE_ATTRIBUTES)valid=false;if(valid)resources[h].push_back({source,prefix});}catch(...){} }
 // Group only validated catalog entries, by their explicit character label.
 std::ifstream catalog(paletteRoot+L"hair_colors.tsv");
 std::map<std::string,std::vector<uint32_t>> groups;
 while(std::getline(catalog,line)){
  std::istringstream row(line);std::string hair,id,label;
  if(!std::getline(row,hair,'\t')||!std::getline(row,id,'\t')||!std::getline(row,label))continue;
  if(!label.empty()&&label.back()=='\r')label.pop_back();
  if(hair.size()!=8||label.size()!=12||label.substr(3,6)!="_HAIR_")continue;
  try{auto h=static_cast<uint32_t>(std::stoul(hair,nullptr,16));if(resources.count(h))groups[label.substr(0,3)].push_back(h);}catch(...){}
 }
 for(auto& group:groups){auto& hairs=group.second;std::sort(hairs.begin(),hairs.end());hairs.erase(std::unique(hairs.begin(),hairs.end()),hairs.end());for(auto h:hairs)battleHairRoutes[h]=hairs;}
 log("HAIR COLOR battle inheritance characters="+std::to_string(groups.size())+" hairstyles="+std::to_string(battleHairRoutes.size()));
 settings=gameRoot+L"REDELBE_LR\\HairColors.prototype.ini";
}
static bool pointerOver(){auto w=window.load();if(!w||!IsWindowVisible(w))return false;POINT p;RECT r;return GetCursorPos(&p)&&GetWindowRect(w,&r)&&PtInRect(&r,p);}
static std::wstring key(uint32_t chara,unsigned slot){return wide(hex(chara))+L"_slot_"+std::to_wstring(slot);}
static int savedColor(uint32_t chara,unsigned slot,uint32_t hair){
 unsigned saved=GetPrivateProfileIntW(L"Colors16",(key(chara,slot)+L"_hair_"+wide(hex(hair))).c_str(),999,settings.c_str());
 if(saved==999)saved=GetPrivateProfileIntW(L"Colors16",key(chara,slot).c_str(),999,settings.c_str());
 if(saved==999){static const unsigned legacy[]={0,5,8,13,6,15,1};auto old=GetPrivateProfileIntW(L"Colors",key(chara,slot).c_str(),0,settings.c_str());saved=old<7?legacy[old]:0;}
 return saved<16?static_cast<int>(saved):0;
}
static void bindPlayer(unsigned side,uint32_t chara,uint32_t hair){
 if(side>1)return;
 battleHair[side]=false;
 auto previous=players[side];
 if(slotRead.character==chara&&slotRead.hair==hair&&GetTickCount64()-slotRead.at<1000){
  players[side]={chara,hair,slotRead.slot,savedColor(chara,slotRead.slot,hair),true};
 }else if(previous.character!=chara||previous.hair!=hair)players[side]={chara,hair,0,0,false};
 auto& p=players[side];
 log("HAIR COLOR BIND P"+std::to_string(side+1)+" char="+hex(chara)+" hair="+hex(hair)+" slot="+(p.known?std::to_string(p.slot):"unknown")+" color="+std::to_string(p.color));
}
static void sync(bool apply,bool show,uint32_t hair,uint32_t chara,unsigned slot){
 bool previousContext=context;context=apply&&resources.count(hair)!=0;activeHair=context?hair:0;visible=show&&context;if(!visible)expanded=false;
 if(!context)return;
 if(currentCharacter!=chara||currentSlot!=slot||currentHair!=hair){int old=current;currentCharacter=chara;currentSlot=slot;currentHair=hair;unsigned saved=GetPrivateProfileIntW(L"Colors16",(key(chara,slot)+L"_hair_"+wide(hex(hair))).c_str(),999,settings.c_str());if(saved==999)saved=GetPrivateProfileIntW(L"Colors16",key(chara,slot).c_str(),999,settings.c_str());if(saved==999){static const unsigned legacy[]={0,5,8,13,6,15,1};unsigned oldSaved=GetPrivateProfileIntW(L"Colors",key(chara,slot).c_str(),0,settings.c_str());saved=oldSaved<7?legacy[oldSaved]:0;}current=saved<16?saved:0;pending=-1;focus=current.load();if(old||current)refresh=true;}
 if(!previousContext&&current)refresh=true;
 DWORD pid=0;auto w=GetForegroundWindow();GetWindowThreadProcessId(w,&pid);if(pid==GetCurrentProcessId()&&w!=window){gameWindow=w;if(!started){started=true;auto t=CreateThread(nullptr,0,thread,nullptr,0,nullptr);if(t)CloseHandle(t);}}
}
static std::wstring select(const std::wstring& path){
 if(context){
  if(!current)return L"";
  auto it=resources.find(activeHair);if(it==resources.end())return L"";
  for(auto& entry:it->second)if(entry.first==path)return entry.second+names[current]+L".file";
  return L"";
 }
 // A global file override cannot isolate two different colors of one shared
 // texture. Keep vanilla for conflicts rather than tinting the wrong fighter.
 std::wstring chosen;int choice=-1;
 for(unsigned side=0;side<2;++side){
  const auto& player=players[side];
  const std::vector<uint32_t> selectedOnly{player.hair};
  auto route=battleHairRoutes.find(player.hair);
  const auto& hairs=battleHair[side]&&route!=battleHairRoutes.end()?route->second:selectedOnly;
  for(auto hair:hairs){
   if(!hair)continue;
   auto it=resources.find(hair);if(it==resources.end())continue;
   for(const auto& entry:it->second)if(entry.first==path){
   int color=player.known?player.color:0;
   if(choice>=0&&choice!=color)return L"";
   choice=color;if(color)chosen=entry.second+names[color]+L".file";
   }
  }
 }
 return chosen;
}
static bool take(){if(refresh&&context){refresh=false;return true;}int value=pending.exchange(-1);if(!context||value<0||value>=16||value==current)return false;if(!tickets::purchaseHair(currentCharacter,currentHair,value)){log("TICKETS hair selection denied: insufficient balance or storage failure");return false;}auto saveKey=key(currentCharacter,currentSlot)+L"_hair_"+wide(hex(currentHair));if(!WritePrivateProfileStringW(L"Colors16",saveKey.c_str(),std::to_wstring(value).c_str(),settings.c_str())){log("HAIR COLOR save failed error="+std::to_string(GetLastError()));return false;}if(GetPrivateProfileIntW(L"Colors16",saveKey.c_str(),999,settings.c_str())!=static_cast<unsigned>(value)){log("HAIR COLOR save verification failed");return false;}current=value;log("HAIR COLOR saved key="+utf8(saveKey)+" color="+std::to_string(value));return true;}
static void pad(DWORD player,XINPUT_STATE* state,DWORD result){
 static WORD previous[4]{},swallowed[4]{};if(player>=4||result!=ERROR_SUCCESS)return;WORD buttons=state->Gamepad.wButtons,edge=buttons&~previous[player];previous[player]=buttons;swallowed[player]&=buttons;
 state->Gamepad.wButtons&=~swallowed[player];if(player!=0||!visible)return;bool block=expanded;bool g=pollG();block=block||g;
 if(edge&XINPUT_GAMEPAD_X){expanded=!expanded;focus=current.load();block=true;}
 static WORD heldDirections[4]{};static ULONGLONG repeatAt[4]{};
 WORD directions=buttons&(XINPUT_GAMEPAD_DPAD_UP|XINPUT_GAMEPAD_DPAD_DOWN|XINPUT_GAMEPAD_DPAD_LEFT|XINPUT_GAMEPAD_DPAD_RIGHT);
 if(state->Gamepad.sThumbLY>16000)directions|=XINPUT_GAMEPAD_DPAD_UP;
 if(state->Gamepad.sThumbLY<-16000)directions|=XINPUT_GAMEPAD_DPAD_DOWN;
 if(state->Gamepad.sThumbLX<-16000)directions|=XINPUT_GAMEPAD_DPAD_LEFT;
 if(state->Gamepad.sThumbLX>16000)directions|=XINPUT_GAMEPAD_DPAD_RIGHT;
 auto now=GetTickCount64();WORD navigation=0;
 if(directions!=heldDirections[player]){navigation=directions;repeatAt[player]=now+300;}
 else if(directions&&now>=repeatAt[player]){navigation=directions;repeatAt[player]=now+90;}
 heldDirections[player]=expanded?directions:0;
 edge=(edge&~(XINPUT_GAMEPAD_DPAD_UP|XINPUT_GAMEPAD_DPAD_DOWN|XINPUT_GAMEPAD_DPAD_LEFT|XINPUT_GAMEPAD_DPAD_RIGHT))|navigation;
 if(expanded&&(navigation||(edge&XINPUT_GAMEPAD_X))){hoverPosition=mousePosition();}
 if(expanded){if(edge&XINPUT_GAMEPAD_DPAD_UP)focus=(focus.load()+12)%16;if(edge&XINPUT_GAMEPAD_DPAD_DOWN)focus=(focus.load()+4)%16;if(edge&XINPUT_GAMEPAD_DPAD_LEFT)focus=(focus.load()+15)%16;if(edge&XINPUT_GAMEPAD_DPAD_RIGHT)focus=(focus.load()+1)%16;if(edge&XINPUT_GAMEPAD_A)pending=focus.load();if(edge&XINPUT_GAMEPAD_B)expanded=false;block=true;}
 if(block){swallowed[player]|=buttons;state->Gamepad.wButtons=0;state->Gamepad.sThumbLX=state->Gamepad.sThumbLY=0;state->Gamepad.bLeftTrigger=state->Gamepad.bRightTrigger=0;}
}
static void keyboard(unsigned char* keys){
 static unsigned char swallowed[256]{};
 static bool oldH=false,oldUp=false,oldDown=false,oldLeft=false,oldRight=false,oldA=false,oldB=false;
 bool h=pollG(),up=(keys[0xc8]&0x80)!=0,down=(keys[0xd0]&0x80)!=0,left=(keys[0xcb]&0x80)!=0,right=(keys[0xcd]&0x80)!=0,a=(keys[0x1c]&0x80)!=0,b=(keys[1]&0x80)!=0;
 for(int i=0;i<256;i++){swallowed[i]&=keys[i];keys[i]&=~swallowed[i];}
 if(visible){bool block=expanded;if(h)block=true;if(expanded){if(up&&!oldUp)focus=(focus.load()+12)%16;if(down&&!oldDown)focus=(focus.load()+4)%16;if(left&&!oldLeft)focus=(focus.load()+15)%16;if(right&&!oldRight)focus=(focus.load()+1)%16;if(a&&!oldA)pending=focus.load();if(b&&!oldB)expanded=false;block=true;}if(block){for(int i=0;i<256;i++)swallowed[i]|=keys[i];memset(keys,0,256);}else keys[0x22]=0;}
 oldH=h;oldUp=up;oldDown=down;oldLeft=left;oldRight=right;oldA=a;oldB=b;
}
}

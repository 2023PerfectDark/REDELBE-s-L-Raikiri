#pragma once
#pragma comment(lib, "user32.lib")
// Experimental main-menu mouse navigation. No disconnected controller is created.
namespace mousemenu {
struct Row { uintptr_t root=0,hitPane=0,leftArrow=0,rightArrow=0; bool enabled=true; };
static std::map<unsigned,Row> rows;
static std::map<uint32_t,std::map<unsigned,Row>> families;
static uint32_t rowHash=0xf326b46d;
static WORD clickAction=XINPUT_GAMEPAD_A;
static int focused=-1,target=-1;
static bool startup=true;
static bool reward=false;
static bool active=false,confirm=false,leftWas=false,rightWas=false;
static POINT lastPoint{-100000,-100000};
static ULONGLONG pulseEnd=0,nextPulse=0,padAt=0;
static ULONGLONG navigateAt=0;
static WORD pulse=0;
static void* menuOwner=nullptr;
static std::map<unsigned,std::string> cursorIn;
static bool hiddenNative=false;
static uintptr_t dialogLayout=0;
static bool dialog=false,wasActive=false;
static int dialogTarget=-1;
static unsigned screen=0; // 0=list, 1=controller side, 2=character grid, 3=stage grid
static uintptr_t costumeLayout=0;
static unsigned costumePlayer=0;
static bool costumeReturning=false;
static int stageSteps=0;
static bool variantAWas=false,variantDWas=false;
static volatile LONG stageWheel=0,stageWheelEnabled=0;
static HHOOK wheelHook=nullptr;
static DWORD wheelThread=0;
static int wheelRemainder=0;
static bool stageHeld=false,stageDragged=false;
static float stageDragY=0,stageStartY=0;
static float stageDragX=0,stageStartX=0;
static int stageDragAxis=0,stageVariantSteps=0;
static int stageVariantDirection=0;
static int horizontalDrag(float x,float& anchor,int& direction) {
 // Follow the furthest point in the accepted direction, so reversing does
 // not require dragging all the way back to the original click position.
 if((direction<0&&x<anchor)||(direction>0&&x>anchor))anchor=x;
 float delta=x-anchor;
 if(abs(delta)<64.f)return 0;
 int next=delta>0?1:-1;
 if(next==direction)return 0;
 direction=next;anchor=x;return next;
}
static LONG stagePointerY=0;
static int dragAxis(float dx,float dy) {
 if(std::max(abs(dx),abs(dy))<=10.f)return 0;
 return abs(dx)>abs(dy)?1:2;
}
static LRESULT CALLBACK wheelMessages(int code,WPARAM removed,LPARAM data) {
 if(code>=0&&removed==PM_REMOVE&&InterlockedCompareExchange(&stageWheelEnabled,0,0)) {
  auto msg=reinterpret_cast<MSG*>(data);
  if(msg&&msg->message==WM_MOUSEWHEEL)InterlockedExchangeAdd(&stageWheel,static_cast<short>(HIWORD(msg->wParam)));
 }
 return CallNextHookEx(wheelHook,code,removed,data);
}
static void resetStageGesture() {
 stageHeld=stageDragged=false;wheelRemainder=0;InterlockedExchange(&stageWheel,0);
 stageDragAxis=0;stageVariantSteps=0;
 stageVariantDirection=0;
 InterlockedExchange(&stageWheelEnabled,0);
}
static int wheelSteps(int delta) {
 wheelRemainder+=delta;int steps=wheelRemainder/WHEEL_DELTA;wheelRemainder%=WHEEL_DELTA;return -steps;
}
static unsigned confirmKey=0x1c,backKey=0x01;
template<class T> static bool read(uintptr_t at,T& out) {
 SIZE_T got=0;return at&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),&out,sizeof(out),&got)&&got==sizeof(out);
}
static uintptr_t rootPane(uintptr_t layout) {
 uintptr_t node=0,root=0;return read(layout+0x28,node)&&node!=layout+0x48&&read(node+0x10,root)?root:0;
}
static bool rowFamily(uint32_t hash){
 switch(hash) {
 case 0xf326b46d:case 0xa37fad03:case 0x63d7b7fc:
 // Additional native list layouts with bounded root hit areas and text focus events.
 case 0xa3b4d739:case 0xb15af686:case 0xe825f3e2:case 0x5a3b25ba:
 case 0x62dcc61e:case 0xeb672ec7:case 0xae476364:case 0xf797a232:
 case 0x4ef39a3f:case 0x534d6e7c:case 0x7454be7b:case 0x8f2023d0:return true;
 default:return false;
 }
}
static uintptr_t paneNamed(uintptr_t layout,const char* wanted) {
 uintptr_t node=0;if(!read(layout+0x28,node))return 0;
 for(unsigned i=0;node&&node!=layout+0x48&&i<512;++i) {
  uintptr_t pane=0,name=0;unsigned short length=0;char text[80]{};
  if(!read(node+0x10,pane))break;
  if(read(pane+0xb0,name)&&read(pane+0x110,length)&&length<sizeof(text)) {
   SIZE_T got=0;if(ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(name),text,length,&got)&&got==length&&!strcmp(text,wanted))return pane;
  }
  if(!read(node+8,node))break;
 }
 return 0;
}
static void restoreFocus();
static void activateRows(void* owner,uint32_t hash,unsigned kind,int selection) {
 if(rowHash!=hash||screen!=kind){target=-1;confirm=false;pulse=0;cursorIn.clear();}
 rowHash=hash;screen=kind;rows=families[hash];active=true;startup=false;
 costumeReturning=false;
 focused=selection;menuOwner=owner;hiddenNative=false;
 log("MOUSE screen="+std::to_string(kind)+" family="+hex(hash)+" focus="+std::to_string(selection));
}
static void animation(void* owner,uint32_t hash,const char* name,unsigned instance) {
 if(!name)return;
 aivsai::animation(hash,name,instance);
 if(hash==0x90d08268) {
  if(!strcmp(name,"unlock_in")) {
   restoreFocus();reward=true;active=false;startup=false;target=-1;confirm=false;pulse=0;
   log("MOUSE rewards open");
  }
  if(!strcmp(name,"unlock_out")) {
   reward=false;pulse=0;confirm=false;target=-1;nextPulse=GetTickCount64()+180;
   log("MOUSE rewards closed");
  }
 }
 if(hash==0xd6c0ffd3&&!strcmp(name,"menu_out")) {
  active=false;target=-1;confirm=false;pulse=0;hiddenNative=false;
 }
 if(hash==0xb281b468) {
  if(!strcmp(name,"in")||!strcmp(name,"loop"))startup=true;
  if(!strcmp(name,"select")||!strcmp(name,"out")){startup=false;pulse=0;confirm=false;target=-1;}
 }
 if(hash==0x8d9b36bc) {
  if(!strcmp(name,"in")) {
   wasActive=active;restoreFocus();dialog=true;active=false;startup=false;
   dialogLayout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,instance));
   target=-1;dialogTarget=-1;confirm=false;pulse=0;
  }
  if(!strcmp(name,"out")) {dialog=false;active=wasActive;dialogTarget=-1;confirm=false;pulse=0;nextPulse=GetTickCount64()+180;}
  return;
 }
 if(dialog||reward)return;
 if(hash==0xa3b4d739&&!strcmp(name,"text_on")) {
  // Result-screen layouts are recreated after a match. Refresh every row so
  // unvisited choices cannot retain pointers from the character menus.
  for(unsigned i=0;i<12;++i){auto layout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,i));auto root=rootPane(layout);
   if(root){auto& row=families[hash][i];if(row.root!=root)row.enabled=true;row.root=row.hitPane=root;row.leftArrow=row.rightArrow=0;}}
  if(rowHash==hash)rows=families[hash];
 }
 if(hash==0xb384f573) {
  if(!strcmp(name,"cos_in_p1")||!strcmp(name,"cos_in_p2")) {
   costumeLayout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,instance));costumePlayer=!strcmp(name,"cos_in_p2")?1:0;
   screen=4;active=true;target=-1;confirm=false;pulse=0;hiddenNative=false;
   costumeReturning=false;
  }
  if(screen==4&&(!strcmp(name,"cos_out_p1")||!strcmp(name,"cos_out_p2"))){active=false;pulse=0;costumeReturning=true;}
 }
 if(hash==0x1b8aa1c4) {
  if(!strcmp(name,"side_in")) {
   auto layout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,instance));
   for(unsigned side=0;side<2;++side){auto pane=paneNamed(layout,side?"PG_controller_off_p2":"PG_controller_off_p1");families[hash][side]={pane,pane,0,0,true};}
   auto center=reinterpret_cast<uintptr_t>(layoutObject(owner,0,0xd01a2042,0));
   auto pane=paneNamed(center,"PG_controller_center_off_p1");if(pane)families[hash][2]={pane,pane,0,0,true};
   activateRows(owner,hash,1,-1);
  }
  if(!strcmp(name,"side_on_p1"))activateRows(owner,hash,1,0);
  if(!strcmp(name,"side_on_p2"))activateRows(owner,hash,1,1);
  if(!strcmp(name,"side_default_p1")||!strcmp(name,"side_default_p2"))activateRows(owner,hash,1,-1);
  if(!strcmp(name,"side_off_p1")||!strcmp(name,"side_off_p2"))activateRows(owner,hash,1,-1);
  if(!strcmp(name,"side_out")){active=false;target=-1;confirm=false;pulse=0;}
  return;
 }
 if(hash==0xf403bcba) {
  // Canceling costume selection resumes the existing portrait cursor with
  // icon_loop, without sending a fresh icon_on event.
  if(costumeReturning&&screen==4&&!active&&
     ((!strcmp(name,"icon_loop_p1")&&costumePlayer==0)||
      (!strcmp(name,"icon_loop_p2")&&costumePlayer==1))) {
   activateRows(owner,hash,2,static_cast<int>(instance));
   nextPulse=GetTickCount64()+180; // Do not carry the cancel into the roster.
  }
  if(!strcmp(name,"icon_in")||!strncmp(name,"icon_on",7)) {
   auto layout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,instance));auto root=rootPane(layout);
   families[hash][instance]={root,root,0,0,true};
   if(hash==rowHash)rows[instance]=families[hash][instance];
  }
  if(!strncmp(name,"icon_on",7))activateRows(owner,hash,hash==0xf403bcba?2:3,static_cast<int>(instance));
  if(!strncmp(name,"icon_select",11)){active=false;target=-1;confirm=false;pulse=0;}
  return;
 }
 if(hash==0xd0805c2d&&!strcmp(name,"stage_sele_base_in")){
  activateRows(owner,0xaf1d7ac5,3,-1);stageSteps=0;resetStageGesture();
  for(unsigned i=0;i<11;++i){auto layout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,0xaf1d7ac5,i));auto root=rootPane(layout);if(root)families[0xaf1d7ac5][i]={root,paneNamed(layout,"icon_stage_1"),0,0,true};}
  rows=families[0xaf1d7ac5];
 }
 if(hash==0xd0805c2d&&!strcmp(name,"stage_sele_base_out")){active=false;target=-1;stageSteps=0;confirm=false;pulse=0;resetStageGesture();}
 if(hash==0xdd6728d2&&!strcmp(name,"detail_in")){costumeReturning=false;active=rowHash==0xe825f3e2;target=-1;confirm=false;pulse=0;}
 if(hash==0xe825f3e2&&!strcmp(name,"cursor_in_p1")) {
  for(unsigned i=0;i<4;++i) {
   auto layout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,i));auto root=rootPane(layout);
   if(root)families[hash][i]={root,root,paneNamed(layout,"setting_arrow_l"),paneNamed(layout,"setting_arrow_r"),true};
  }
  activateRows(owner,hash,0,static_cast<int>(instance));
 }
 if((hash==0x6d610d56&&rowHash==0xf326b46d)||hash==rowHash) {
  if(!strncmp(name,"cursor_",7)&&strstr(name,"_in"))cursorIn[instance]=name;
 }
 if(hash==0x84b536e1) {
  if(!strcmp(name,"menu_in")){startup=false;active=true;screen=0;rowHash=0xf326b46d;rows=families[rowHash];target=-1;confirm=false;}
  if(!strcmp(name,"menu_out")){active=false;target=-1;confirm=false;pulse=0;hiddenNative=false;}
  if(strstr(name,"_open")||strstr(name,"_close")){target=-1;confirm=false;}
 }
 if(!rowFamily(hash))return;
 auto& row=families[hash][instance];
 if(!strcmp(name,"text_in")||!strcmp(name,"text_on")) {
  auto layout=reinterpret_cast<uintptr_t>(layoutObject(owner,0,hash,instance));
  row.root=rootPane(layout);row.hitPane=hash==0x63d7b7fc?paneNamed(layout,"PG_end_menu_text"):row.root;
  row.leftArrow=paneNamed(layout,"setting_arrow_l");row.rightArrow=paneNamed(layout,"setting_arrow_r");
 }
 if(!strcmp(name,"text_default"))row.enabled=true;
 if(!strcmp(name,"text_dimmed"))row.enabled=false;
 if(!strcmp(name,"text_on")) {
  screen=0;
  if(rowHash!=hash){rowHash=hash;rows=families[hash];target=-1;confirm=false;pulse=0;cursorIn.clear();}
  active=true;startup=false;menuOwner=owner;focused=static_cast<int>(instance);hiddenNative=false;
  log("MOUSE focus family="+hex(hash)+" row="+std::to_string(instance));
 }
 if(hash==rowHash)rows[instance]=row;
}
// Suppress only the visual entrance of intermediate native focus steps.
// The native menu selection still advances, so confirming uses its real target.
static bool suppress(void* owner,uint32_t hash,const char* name,unsigned instance) {
 if(!name||screen!=0||rowHash==0xe825f3e2||rowHash==0xa3b4d739||!active||target<0||static_cast<int>(instance)==target)return false;
 if((hash==(rowHash==0xf326b46d?0x6d610d56:rowHash))&&!strncmp(name,"cursor_",7)&&(strstr(name,"_in")||strstr(name,"_loop"))) {
  if(strstr(name,"_in"))cursorIn[instance]=name;
  return true;
 }
 if(hash==rowHash&&!strcmp(name,"text_on")) {
  menuOwner=owner;focused=static_cast<int>(instance);hiddenNative=true;
  log("MOUSE skip intermediate visual="+std::to_string(instance));return true;
 }
 return false;
}
static void restoreFocus() {
 if(!hiddenNative||!active||!menuOwner||focused<0)return;
 auto style=cursorIn.find(static_cast<unsigned>(focused));
 if(style!=cursorIn.end())layoutOriginal(menuOwner,rowHash==0xf326b46d?0x6d610d56:rowHash,style->second.c_str(),static_cast<unsigned>(focused));
 layoutOriginal(menuOwner,rowHash,"text_on",static_cast<unsigned>(focused));hiddenNative=false;
}
struct Hit {int id;float x,y,width,half,leftX,rightX;};
#include "preview_publish.h"
static WORD poll() {
 auto now=GetTickCount64();bool left=(GetAsyncKeyState(VK_LBUTTON)&0x8000)!=0,right=(GetAsyncKeyState(VK_RBUTTON)&0x8000)!=0;
 bool variantA=(GetAsyncKeyState('A')&0x8000)!=0,variantD=(GetAsyncKeyState('D')&0x8000)!=0;
 bool variantLeft=variantA&&!variantAWas,variantRight=variantD&&!variantDWas;
 variantAWas=variantA;variantDWas=variantD;
 bool le=left&&!leftWas,re=right&&!rightWas;leftWas=left;rightWas=right;
 HWND window=GetForegroundWindow();DWORD pid=0;if(window)GetWindowThreadProcessId(window,&pid);
 if((!active&&!startup&&!dialog&&!reward)||pid!=GetCurrentProcessId()){resetStageGesture();stageSteps=0;pulse=0;target=-1;dialogTarget=-1;confirm=false;restoreFocus();return 0;}
 bool stageInput=active&&screen==3&&!dialog&&!reward;
 if(stageInput) {
  DWORD thread=GetWindowThreadProcessId(window,nullptr);
  if(thread!=wheelThread) {
   if(wheelHook)UnhookWindowsHookEx(wheelHook);
   HMODULE module=nullptr;GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(&wheelMessages),&module);
   wheelHook=SetWindowsHookExW(WH_GETMESSAGE,wheelMessages,module,thread);wheelThread=wheelHook?thread:0;
  }
  InterlockedExchange(&stageWheelEnabled,1);
 } else resetStageGesture();
 RECT rect{};POINT point{};
 if(!GetClientRect(window,&rect)||!GetCursorPos(&point)||!ScreenToClient(window,&point)||rect.right<=0||rect.bottom<=0)return 0;
 if(point.x<0||point.y<0||point.x>=rect.right||point.y>=rect.bottom){resetStageGesture();stageSteps=0;target=-1;confirm=false;restoreFocus();return 0;}
 if(startup||(reward&&!dialog)) {
  if(le&&now>=nextPulse){pulse=XINPUT_GAMEPAD_A;pulseEnd=now+65;nextPulse=now+180;}
  return now<pulseEnd?pulse:0;
 }
 // LR's layout coordinates use a centered 1920x1080 canvas.
 float scale=std::min(rect.right/1920.f,rect.bottom/1080.f);
 float x=(point.x-(rect.right-1920.f*scale)*.5f)/scale-960.f;
 float y=540.f-(point.y-(rect.bottom-1080.f*scale)*.5f)/scale;
 bool moved=abs(point.x-lastPoint.x)>2||abs(point.y-lastPoint.y)>2;lastPoint=point;
 if(stageInput&&variantLeft!=variantRight) {
  resetStageGesture();stageSteps=0;confirm=false;
  pulse=variantLeft?XINPUT_GAMEPAD_DPAD_LEFT:XINPUT_GAMEPAD_DPAD_RIGHT;
  pulseEnd=now+65;nextPulse=now+180;
  return pulse;
 }
 if(screen==4&&!dialog) {
  WORD action=0;
  const char* p1[]={"cos_cursor_p1","cos_arrow_up_p1","cos_arrow_down_p1"};
  const char* p2[]={"cos_cursor_p2","cos_arrow_up_p2","cos_arrow_down_p2"};
  for(unsigned i=0;i<3;++i) {
   uintptr_t pane=paneNamed(costumeLayout,costumePlayer?p2[i]:p1[i]),mp=0;float m[16]{};short size[2]{};unsigned char anchor=0;
   if(!pane||!read(pane+0xe0,mp)||!read(mp,m)||!read(pane+0xf0,size)||!read(pane+0x10c,anchor))continue;
   float w=abs(m[0])*size[0],h=abs(m[5])*size[1],edge=m[12];
   if((anchor>>4)==1)edge-=w*.5f;else if((anchor>>4)==2)edge-=w;
   if(w>0&&h>0&&x>=edge&&x<=edge+w&&abs(y-m[13])<=h*.5f)action=i==0?XINPUT_GAMEPAD_A:i==1?XINPUT_GAMEPAD_DPAD_UP:XINPUT_GAMEPAD_DPAD_DOWN;
  }
  if(re)action=XINPUT_GAMEPAD_B;else if(!le)action=0;
  if(action&&now>=nextPulse){pulse=action;pulseEnd=now+65;nextPulse=now+180;}
  return now<pulseEnd?pulse:0;
 }
 if(dialog) {
  // Dialogs use separate layouts: never navigate the obscured menu underneath.
  int hit=-1,selected=-1;unsigned bestAlpha=0;
  const char* plates[]={"plate_title_l_0001","plate_title_l_0000"};
  for(int side=0;side<2;++side) {
   uintptr_t pane=paneNamed(dialogLayout,plates[side]),mp=0;float m[16]{};short size[2]{};unsigned char anchor=0,alpha=0;
   if(!pane||!read(pane+0xe0,mp)||!read(mp,m)||!read(pane+0xf0,size)||!read(pane+0x10c,anchor)||!read(pane+0x113,alpha))continue;
   float w=abs(m[0])*size[0],h=abs(m[5])*size[1],edge=m[12];
   if((anchor>>4)==1)edge-=w*.5f;else if((anchor>>4)==2)edge-=w;
   if(w>0&&h>0&&x>=edge&&x<=edge+w&&abs(y-m[13])<=h*.5f)hit=side;
   if(alpha>bestAlpha){bestAlpha=alpha;selected=side;}
  }
  if(re){dialogTarget=-1;confirm=false;pulse=XINPUT_GAMEPAD_B;pulseEnd=now+65;nextPulse=now+180;}
  else if(le&&hit>=0){dialogTarget=hit;confirm=true;}
  else if(moved&&!confirm&&hit>=0)dialogTarget=hit;
  if(now<pulseEnd)return pulse;
  pulse=0;if(now<nextPulse||dialogTarget<0||selected<0)return 0;
  if(dialogTarget!=selected)pulse=dialogTarget==0?XINPUT_GAMEPAD_DPAD_LEFT:XINPUT_GAMEPAD_DPAD_RIGHT;
  else if(confirm){pulse=XINPUT_GAMEPAD_A;confirm=false;dialogTarget=-1;}else return 0;
  pulseEnd=now+65;nextPulse=now+180;return pulse;
 }
 std::vector<Hit> visible;
 for(const auto& item:rows) {
  auto r=item.second;if(!r.enabled||!r.root)continue;
  unsigned char alpha=0;uint32_t flags=0;uintptr_t matrix=0;float m[16]{};
  if(!read(r.root+0x113,alpha)||((screen==0||screen==3)&&alpha<240)||!read(r.root+0x104,flags)||!(flags&0x20)||!read(r.root+0xe0,matrix)||!read(matrix,m))continue;
  if(m[12]<-960||m[12]>960||m[13]<-540||m[13]>540)continue;
  float width=512.f,height=48.f,leftEdge=m[12],cy=m[13],lx=10000,rx=10000;
  if(rowHash!=0xf326b46d) {
   uintptr_t hm=0;float matrixData[16]{};short size[2]{};unsigned char anchor=0;
   if(!r.hitPane||!read(r.hitPane+0xe0,hm)||!read(hm,matrixData)||!read(r.hitPane+0xf0,size)||!read(r.hitPane+0x10c,anchor))continue;
   width=abs(matrixData[0])*size[0];height=abs(matrixData[5])*size[1];leftEdge=matrixData[12];cy=matrixData[13];
   if((anchor>>4)==1)leftEdge-=width*.5f;else if((anchor>>4)==2)leftEdge-=width;
   if(width<=0||height<=0)continue;
  }
  for(unsigned side=0;side<2;++side){uintptr_t am=0;float av[16]{};auto pane=side?r.rightArrow:r.leftArrow;
   if(pane&&read(pane+0xe0,am)&&read(am,av)){if(side)rx=av[12];else lx=av[12];}}
  visible.push_back({static_cast<int>(item.first),leftEdge,cy,width,height*.5f,lx,rx});
 }
 std::sort(visible.begin(),visible.end(),[](const Hit&a,const Hit&b){return a.y>b.y;});
 if(visible.empty()){target=-1;confirm=false;pulse=0;return 0;}
 int hit=-1;WORD action=XINPUT_GAMEPAD_A;float bestDistance=1.e30f;
 for(size_t i=0;i<visible.size();++i) {
  const auto&r=visible[i];float half=r.half;
  if(x>=r.x&&x<=r.x+r.width&&y>=r.y-half&&y<=r.y+half){
   float dx=x-(r.x+r.width*.5f),dy=y-r.y,distance=dx*dx+dy*dy;
   if(distance<bestDistance){bestDistance=distance;hit=r.id;action=XINPUT_GAMEPAD_A;if(abs(x-r.leftX)<=32)action=XINPUT_GAMEPAD_DPAD_LEFT;else if(abs(x-r.rightX)<=32)action=XINPUT_GAMEPAD_DPAD_RIGHT;}
   if(screen<2)break;
  }
 }
 if(screen==3) {
  // Stage rows are recycled as the list scrolls. Queue relative moves, not a
  // permanent instance ID that would refer to a different stage after scrolling.
  int scroll=wheelSteps(static_cast<int>(InterlockedExchange(&stageWheel,0)));
  if(scroll){stageSteps=std::clamp(stageSteps+scroll,-10,10);confirm=false;stageDragged=true;}
  if(le){stageHeld=true;stageDragged=false;stageDragAxis=0;stageVariantSteps=0;stageVariantDirection=0;stagePointerY=point.y;stageDragX=stageStartX=x;stageDragY=stageStartY=y;confirm=false;}
  if(stageHeld&&left) {
   if(!stageDragAxis)stageDragAxis=dragAxis(x-stageStartX,y-stageStartY);
   if(stageDragAxis)stageDragged=true;
   if(stageDragAxis==1) {
    // Keep the visible pointer on the starting horizontal line while held.
    POINT locked{point.x,stagePointerY};
    if(point.y!=stagePointerY&&ClientToScreen(window,&locked))SetCursorPos(locked.x,locked.y);
    if(!stageVariantSteps) {
     int direction=horizontalDrag(x,stageDragX,stageVariantDirection);
     if(direction){stageVariantSteps=direction;stageSteps=0;confirm=false;}
    }
   }
   int steps=stageDragAxis==2?static_cast<int>((y-stageDragY)/32.f):0;
   if(steps){
    if((steps>0&&stageSteps<0)||(steps<0&&stageSteps>0))stageSteps=0;
    stageSteps=std::clamp(stageSteps+steps,-3,3);stageDragY+=steps*32.f;confirm=false;
   }
  }
  bool clicked=stageHeld&&!left&&!stageDragged;
  if(stageHeld&&!left&&stageDragged){stageSteps=0;stageVariantSteps=0;}
  if(!left)stageHeld=false;
  if(re){resetStageGesture();stageSteps=0;confirm=false;pulse=XINPUT_GAMEPAD_B;pulseEnd=now+65;nextPulse=now+180;}
  else if(hit>=0&&clicked) {
   auto chosen=std::find_if(visible.begin(),visible.end(),[&](const Hit&r){return r.id==hit;});
   auto selected=std::max_element(visible.begin(),visible.end(),[](const Hit&a,const Hit&b){return a.width<b.width;});
   stageSteps=static_cast<int>(chosen-selected);confirm=true;navigateAt=now;
  }
  if(now<pulseEnd)return pulse;
  pulse=0;if(now<nextPulse)return 0;
  if(stageVariantSteps){pulse=stageVariantSteps>0?XINPUT_GAMEPAD_DPAD_RIGHT:XINPUT_GAMEPAD_DPAD_LEFT;stageVariantSteps=0;}
  else if(stageSteps){pulse=stageSteps>0?XINPUT_GAMEPAD_DPAD_DOWN:XINPUT_GAMEPAD_DPAD_UP;stageSteps+=stageSteps>0?-1:1;}
  else if(confirm){pulse=XINPUT_GAMEPAD_A;confirm=false;}else return 0;
  const bool dragging=stageHeld&&stageDragged&&!confirm&&
   (pulse==XINPUT_GAMEPAD_DPAD_UP||pulse==XINPUT_GAMEPAD_DPAD_DOWN);
  pulseEnd=now+(dragging?32:65);nextPulse=now+(dragging?90:220);return pulse;
 }
 if(re){target=-1;confirm=false;pulse=XINPUT_GAMEPAD_B;pulseEnd=now+65;nextPulse=now+180;}
 else if(le&&hit>=0){target=hit;confirm=true;clickAction=action;navigateAt=now;}
 else if(moved&&!confirm&&hit>=0){if(target!=hit)navigateAt=now;target=hit;}
 if(target>=0&&now-navigateAt>2000){target=-1;confirm=false;pulse=0;restoreFocus();return 0;}
 if(now<pulseEnd)return pulse;
 pulse=0;if(now<nextPulse)return 0;
 if(target<0){restoreFocus();return 0;}
 auto a=std::find_if(visible.begin(),visible.end(),[](const Hit&r){return r.id==focused;});
 auto b=std::find_if(visible.begin(),visible.end(),[](const Hit&r){return r.id==target;});
 if(screen==1&&target==2) {
  if(focused<0){if(confirm)aivsai::request(now);confirm=false;target=-1;return 0;}
  pulse=focused==0?XINPUT_GAMEPAD_DPAD_RIGHT:XINPUT_GAMEPAD_DPAD_LEFT;pulseEnd=now+65;nextPulse=now+180;return pulse;
 }
 if(screen==1&&a==visible.end()&&b!=visible.end()){pulse=target==0?XINPUT_GAMEPAD_DPAD_LEFT:XINPUT_GAMEPAD_DPAD_RIGHT;pulseEnd=now+65;nextPulse=now+180;return pulse;}
 if(a==visible.end()||b==visible.end()){target=-1;confirm=false;restoreFocus();return 0;}
 if(a==b){restoreFocus();if(!confirm)return 0;confirm=false;target=-1;pulse=clickAction;}
 else if(abs(a->y-b->y)<8)pulse=b->x<a->x?XINPUT_GAMEPAD_DPAD_LEFT:XINPUT_GAMEPAD_DPAD_RIGHT;
 else pulse=b<a?XINPUT_GAMEPAD_DPAD_UP:XINPUT_GAMEPAD_DPAD_DOWN;
 const bool moving=(pulse&(XINPUT_GAMEPAD_DPAD_UP|XINPUT_GAMEPAD_DPAD_DOWN))!=0||
  (screen!=0&&(pulse&(XINPUT_GAMEPAD_DPAD_LEFT|XINPUT_GAMEPAD_DPAD_RIGHT))!=0);
 const bool quick=moving&&rowHash!=0xa3b4d739;
 pulseEnd=now+(quick?18:65);nextPulse=now+(quick?36:180);return pulse;
}
static void pad(DWORD player,XINPUT_STATE* state,DWORD result) {
 patternparts::observe();
 if(player!=0||result!=ERROR_SUCCESS)return;
 std::lock_guard<std::recursive_mutex> guard(mutex);padAt=GetTickCount64();
 publishStageVideo();
 WORD native=state->Gamepad.wButtons,buttons=native;
 if(native){resetStageGesture();target=-1;dialogTarget=-1;stageSteps=0;confirm=false;pulse=0;restoreFocus();}
 else buttons=poll();
 buttons=aivsai::input(buttons,GetTickCount64());
 if(buttons!=native||buttons){state->Gamepad.wButtons=buttons;state->dwPacketNumber+=static_cast<DWORD>(GetTickCount64()/16);}
}
static void keyboard(unsigned char* keys) {
 patternparts::observe();
 std::lock_guard<std::recursive_mutex> guard(mutex);
 publishStageVideo();
 if(GetTickCount64()-padAt<250)return;
 WORD buttons=poll();
 if(aivsai::sideOpen){if(keys[confirmKey]&0x80)buttons|=XINPUT_GAMEPAD_A;if(keys[backKey]&0x80)buttons|=XINPUT_GAMEPAD_B;buttons=aivsai::input(buttons,GetTickCount64());if(aivsai::phase){keys[confirmKey]=keys[backKey]=0;}}
 if(buttons&XINPUT_GAMEPAD_A)keys[confirmKey]=0x80;
 if(buttons&XINPUT_GAMEPAD_B)keys[backKey]=0x80;
 if(buttons&XINPUT_GAMEPAD_DPAD_LEFT)keys[0xcb]=0x80;
 if(buttons&XINPUT_GAMEPAD_DPAD_RIGHT)keys[0xcd]=0x80;
 if(buttons&XINPUT_GAMEPAD_DPAD_UP)keys[0xc8]=0x80;
 if(buttons&XINPUT_GAMEPAD_DPAD_DOWN)keys[0xd0]=0x80;
}
}


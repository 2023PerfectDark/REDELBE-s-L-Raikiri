#define NOMINMAX
#include <windows.h>
#include <xinput.h>
#include <map>
#include <vector>
#include <string>
#include <algorithm>
#include <mutex>
#include <cassert>
static std::recursive_mutex mutex;
static std::string hex(unsigned){return "test";}
static void log(const std::string&){}
static void* layoutObject(void*,int,unsigned,unsigned){return nullptr;}
static int calls=0;
static uintptr_t layoutOriginal(void*,unsigned,const char*,unsigned){++calls;return 0;}
#include "ai_versus_state.h"
#include "pattern_parts_state.h"
#include "mouse_menu.h"
int main(){
 using namespace mousemenu;
 float dragAnchor=500;int dragDirection=0;
 assert(horizontalDrag(430,dragAnchor,dragDirection)==-1);
 assert(horizontalDrag(300,dragAnchor,dragDirection)==0);
 assert(horizontalDrag(200,dragAnchor,dragDirection)==0);
 assert(horizontalDrag(220,dragAnchor,dragDirection)==0);
 assert(horizontalDrag(270,dragAnchor,dragDirection)==1);
 assert(horizontalDrag(400,dragAnchor,dragDirection)==0);
 assert(horizontalDrag(330,dragAnchor,dragDirection)==-1);
 assert(dragAxis(5,5)==0);
 assert(dragAxis(50,12)==1&&dragAxis(-50,12)==1);
 assert(dragAxis(12,50)==2&&dragAxis(12,-50)==2);
 resetStageGesture();
 assert(wheelSteps(60)==0&&wheelSteps(60)==-1);
 assert(wheelSteps(-240)==2);
 stageHeld=true;stageDragged=true;wheelSteps(60);resetStageGesture();
 assert(!stageHeld&&!stageDragged&&wheelSteps(60)==0);
 resetStageGesture();
 active=true;rowHash=0xa3b4d739;focused=2;target=0;
 assert(!suppress((void*)1,0xa3b4d739,"cursor_in_p1",1));
 assert(!suppress((void*)1,0xa3b4d739,"text_on",1));
 rowHash=0xf326b46d;
 animation((void*)1,0x90d08268,"unlock_in",0);
 assert(reward&&!active&&!startup&&target==-1);
 animation((void*)1,0xa3b4d739,"text_on",2);
 assert(!active); // Reward popup blocks underlying menu focus.
 animation((void*)1,0x90d08268,"unlock_out",0);
 assert(!reward&&!active&&pulse==0);
 active=true;confirm=true;target=1;
 animation((void*)1,0xd6c0ffd3,"menu_out",0);
 assert(!active&&!confirm&&target==-1);
 active=true;focused=0;target=12;
 assert(suppress((void*)1,0x6d610d56,"cursor_m_in",7));
 assert(suppress((void*)1,0xf326b46d,"text_on",7));
 assert(focused==7&&hiddenNative&&calls==0);
 assert(!suppress((void*)1,0x6d610d56,"cursor_m_in",12));
 assert(!suppress((void*)1,0xf326b46d,"text_on",12));
 animation((void*)1,0xf326b46d,"text_on",12);
 assert(focused==12&&!hiddenNative);
 target=19;
 assert(suppress((void*)1,0xf326b46d,"text_on",7));
 target=-1;restoreFocus();assert(calls==2&&!hiddenNative);
 assert(!suppress((void*)1,0xf326b46d,"text_on",7));
 active=false;target=12;assert(!suppress((void*)1,0xf326b46d,"text_on",7));
 active=true;target=12;confirm=true;
 animation((void*)1,0x8d9b36bc,"in",0);
 assert(dialog&&!active&&target==-1&&!confirm);
 animation((void*)1,0xa37fad03,"text_on",3);
 assert(rowHash==0xf326b46d); // Background focus must not take over a modal.
 animation((void*)1,0x8d9b36bc,"out",0);
 assert(!dialog&&active&&!confirm&&pulse==0);
 active=false;
 animation((void*)1,0x8d9b36bc,"in",0);
 animation((void*)1,0x8d9b36bc,"out",0);
 assert(!active); // A dialog over gameplay must not reactivate stale menus.
 animation((void*)1,0x1b8aa1c4,"side_in",0);
 assert(active&&screen==1&&focused==-1);
 animation((void*)1,0x1b8aa1c4,"side_on_p2",0);
 assert(focused==1);
 animation((void*)1,0x1b8aa1c4,"side_out",0);
 assert(!active);
 animation((void*)1,0x63d7b7fc,"text_on",4);
 target=9;confirm=true;
 animation((void*)1,0xf403bcba,"icon_on_p1",12);
 assert(active&&screen==2&&focused==12&&target==-1&&!confirm);
 animation((void*)1,0xf403bcba,"icon_select_p1",12);
 assert(!active);
 animation((void*)1,0xb384f573,"cos_in_p1",0);
 assert(active&&screen==4&&target==-1&&!confirm);
 animation((void*)1,0xf403bcba,"icon_loop_p1",12);
 assert(screen==4); // Background loop must not steal costume input.
 animation((void*)1,0xb384f573,"cos_out_p1",0);
 assert(!active);
 animation((void*)1,0xf403bcba,"icon_loop_p1",12);
 assert(active&&screen==2&&focused==12&&pulse==0&&!costumeReturning);
 animation((void*)1,0xb384f573,"cos_in_p2",0);
 animation((void*)1,0xb384f573,"cos_out_p2",0);
 animation((void*)1,0xf403bcba,"icon_loop_p1",12);
 assert(!active&&screen==4); // Other player's cursor cannot resume input.
 animation((void*)1,0xf403bcba,"icon_loop_p2",19);
 assert(active&&screen==2&&focused==19);
 animation((void*)1,0xb384f573,"cos_in_p1",0);
 animation((void*)1,0xdd6728d2,"detail_in",0);
 assert(!active);
 animation((void*)1,0xf403bcba,"icon_loop_p1",12);
 assert(!active); // Accessories transition must not reopen the roster.
 aivsai::available=true;
 aivsai::animation(0xf326b46d,"text_select",3);
 aivsai::animation(0x1b8aa1c4,"side_in");
 assert(aivsai::input(XINPUT_GAMEPAD_A,1000)==XINPUT_GAMEPAD_DPAD_LEFT);
 assert(aivsai::cpuBoth==1);
 assert(aivsai::input(0,1100)==0);
 aivsai::animation(0x1b8aa1c4,"side_on_p1");
 assert(aivsai::input(0,1200)==XINPUT_GAMEPAD_A);
 assert(aivsai::input(0,1220)==XINPUT_GAMEPAD_A);
 assert(aivsai::input(0,1270)==0);
 aivsai::animation(0x1b8aa1c4,"side_out");
 assert(aivsai::cpuBoth==1&&!aivsai::sideOpen);
 aivsai::animation(0x84b536e1,"menu_in");
 assert(!aivsai::cpuBoth);
 patternparts::ResultState rewards;
 rewards.observe(true,11,22,0,0);
 assert(rewards.consume(0,0)==0);
 assert(rewards.consume(1,0)==1);
 assert(rewards.consume(1,0)==0); // Repeated result queries cannot award twice.
 rewards.observe(true,11,22,1,0);
 assert(rewards.consume(1,1)==2); // Loss after a previous win, not total comparison.
 assert(rewards.consume(2,1)==1);
 assert(rewards.consume(3,2)==0); // Ambiguous simultaneous score change.
 rewards.observe(true,11,22,0,0);
 assert(rewards.consume(0,1)==2); // A new set with the same characters rearms.
 rewards.observe(false,11,22,0,1);
 assert(rewards.consume(1,1)==0); // Other modes cannot award parts.
}

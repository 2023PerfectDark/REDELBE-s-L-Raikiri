#pragma once
namespace aivsai {
static bool available=false,sideOpen=false,neutral=true,confirmWas=false;
static bool versusRoute=false;
static volatile BYTE cpuBoth=0;
static volatile BYTE fighterCpu[2]{};
static volatile ULONG cpuGeneration=0;
static unsigned phase=0;
static ULONGLONG began=0;
static void reset(){cpuBoth=0;phase=0;sideOpen=false;neutral=true;}
static void request(ULONGLONG now) {
 if(!available||!versusRoute||!sideOpen||!neutral||phase)return;
 cpuBoth=1;phase=1;began=now;
 log("AI VS AI middle confirmed; preparing offline Versus");
}
static void animation(uint32_t hash,const char* name,unsigned instance=0) {
 if(!name)return;
 if(hash==0x84b536e1&&!strcmp(name,"menu_in")){reset();versusRoute=false;return;}
 if(hash==0xf326b46d&&(!strcmp(name,"text_on")||!strcmp(name,"text_select")))versusRoute=instance==3;
 if(hash!=0x1b8aa1c4)return;
 if(!strcmp(name,"side_in")){reset();sideOpen=true;}
 if(!strcmp(name,"side_default_p1")||!strcmp(name,"side_default_p2")||!strcmp(name,"side_off_p1")||!strcmp(name,"side_off_p2"))neutral=true;
 if(!strcmp(name,"side_on_p1")||!strcmp(name,"side_on_p2")){neutral=false;if(!phase)cpuBoth=0;}
 if(!strcmp(name,"side_out")){sideOpen=false;phase=0;log(cpuBoth?"AI VS AI selected":"AI VS AI off; normal control");}
}
static WORD input(WORD buttons,ULONGLONG now) {
 bool edge=(buttons&XINPUT_GAMEPAD_A)&&!confirmWas;confirmWas=(buttons&XINPUT_GAMEPAD_A)!=0;
 if(!available||!sideOpen)return buttons;
 if(buttons&XINPUT_GAMEPAD_B){cpuBoth=0;phase=0;return buttons;}
 if(edge&&neutral&&!phase)request(now);
 if(!phase)return buttons;
 if(now-began>2000){cpuBoth=0;phase=0;log("AI VS AI side transition timed out; disabled");return 0;}
 if(phase==2)return now-began<65?XINPUT_GAMEPAD_A:0;
 // The native menu rejects a neutral controller. Use its ordinary left-side
 // setup path, then override only the two CPU flags in the match snapshot.
 if(now-began<65)return XINPUT_GAMEPAD_DPAD_LEFT;
 if(neutral||now-began<180)return 0;
 if(phase==1){phase=2;began=now;return XINPUT_GAMEPAD_A;}
 return now-began<65?XINPUT_GAMEPAD_A:0;
}
}

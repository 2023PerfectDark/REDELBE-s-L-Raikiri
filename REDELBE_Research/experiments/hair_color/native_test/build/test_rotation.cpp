#include <windows.h>
#include <Xinput.h>
#include <cmath>
#include <cassert>
#include <iostream>
using std::abs;
static int wardrobePortrait=-1;
static bool wardrobeOpen=false,rotateHeld=false;
static float rotateLastX=0;
static WORD rotateButton=0;
static ULONGLONG rotateUntil=0;
static void resetRotation(){rotateHeld=false;rotateButton=0;rotateUntil=0;}

static WORD rotationStep(float x,bool held,ULONGLONG now){
 if(!held){resetRotation();return 0;}
 float dx=x-rotateLastX;
 if(abs(dx)>=1.f){rotateLastX=x;rotateButton=dx<0?XINPUT_GAMEPAD_LEFT_SHOULDER:XINPUT_GAMEPAD_RIGHT_SHOULDER;rotateUntil=now+45;}
 return now<rotateUntil?rotateButton:0;
}

int main(){rotateHeld=true;rotateLastX=0;assert(rotationStep(12,true,100)==XINPUT_GAMEPAD_RIGHT_SHOULDER);assert(rotationStep(12,true,120)==XINPUT_GAMEPAD_RIGHT_SHOULDER);assert(rotationStep(12,true,150)==0);assert(rotationStep(2,true,160)==XINPUT_GAMEPAD_LEFT_SHOULDER);assert(rotationStep(2,false,161)==0);assert(!rotateHeld&&rotateButton==0);std::cout<<"rotation direction, expiry, reversal and release passed\n";}
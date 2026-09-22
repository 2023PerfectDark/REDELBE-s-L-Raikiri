#include "roster_fade.h"
#include <cassert>
#include <cmath>
#include <iostream>
int main(){
 RosterFadeHover h;h.begin(1);
 assert(h.alpha(1,0,10000)==1);assert(h.alpha(2,0,10000)==0);
 assert(std::abs(h.alpha(2,5000,10000)-0.5f)<0.001f);
 h.leave(1,2000);assert(h.alpha(1,2000,10000)==0);
 assert(std::abs(h.alpha(1,6000,10000)-0.5f)<0.001f);
 h.enter(2,2000);assert(h.alpha(2,2000,10000)==1);
 h.enter(3,3000);assert(h.alpha(2,3000,10000)==0);assert(h.alpha(3,3000,10000)==1);
 h.leave(2,4000);assert(h.focused==3);
 h.enter(1,9500);assert(h.alpha(1,9500,10000)==1);
 h.leave(1,9999);assert(h.alpha(1,9999,10000)==0);assert(h.alpha(1,10000,10000)==1);
 h.begin(4);assert(h.departed.empty());assert(h.alpha(2,0,10000)==0);
 assert(RosterFadeHover::ramp(0,0)==1);
 std::cout<<"PASS: 10s fade, hover reveal, departure/refade, cursor handoff, stale off, completion/reset\n";
}

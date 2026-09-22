#include "battle_hud.h"
#include <cassert>
#include <iostream>
int main(){
 BattleHudState s;constexpr uint32_t health=0x68c58d27,training=0xe3ec1bc9,roster=0xf403bcba;
 assert(!s.hidden);assert(!s.input(false,true));assert(!s.input(true,false));assert(!s.hidden);
 s.input(false,true);assert(s.input(true,true));assert(s.hidden);assert(!s.input(true,true));
 s.bind(1);assert(!s.show(health));assert(s.show(roster));s.hide(training);assert(!s.restore(training));assert(s.restore(health));
 s.input(false,true);assert(s.input(true,true));assert(!s.hidden);assert(s.show(health));assert(!s.restore(training));
 s.bind(2);assert(s.restore(training));assert(s.owner==2);s.bind(0);assert(s.owner==2);
 for(auto h:battleHudLayouts)assert(BattleHudState::contains(h));assert(!BattleHudState::contains(roster));
 std::cout<<"PASS: F5 edges, disabled switch, HUD scope, native hide preservation, owner reset\n";
}

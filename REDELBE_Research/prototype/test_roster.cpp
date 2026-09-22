#include "layer2_roster.h"
#include <cassert>
#include <iostream>
int main() {
    Layer2Roster s;
    s.animation(s.portraits,"icon_in");assert(!s.hidden);
    s.animation(0xdd6728d2,"detail_in");assert(s.hidden);
    s.animation(s.portraits,"icon_loop_p1");assert(s.hidden);
    s.animation(0xdd6728d2,"detail_out");assert(s.hidden);
    s.animation(s.portraits,"icon_on_p2");assert(!s.hidden);
    s.animation(0xdd6728d2,"detail_in");assert(s.hidden);
    s.animation(0xdd6728d2,"detail_out");assert(s.hidden);
    s.animation(0,"menu_in");assert(s.hidden);
    s.animation(0xb384f573,"cos_in_p2");assert(!s.hidden);
    s.animation(0xdd6728d2,"detail_in");assert(s.hidden);
    s.animation(s.portraits,"icon_on_p1");assert(!s.hidden);
    s.animation(0xdd6728d2,"detail_in");assert(s.hidden);
    s.animation(s.portraits,"icon_in");assert(!s.hidden);
    s.animation(0,"detail_in");assert(!s.hidden);
    std::cout<<"PASS: Accessories, next player, all ready, cancel, reentry, unrelated layout\n";
}

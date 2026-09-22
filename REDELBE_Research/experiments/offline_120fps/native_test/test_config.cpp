#include "user_config.h"
#include <sstream>
#include <cassert>
#include <iostream>
int main(){
 userconfig::Settings s;
 assert(s.flag("UI","character_roster_transitions"));
 std::istringstream in("\xef\xbb\xbf[UI]\ncharacter_roster_transitions = FALSE ; comment\nroster_fade_ms=10000\nroster_handoff=INSTANT\n[Misc]\nsurvival_stage=\"My # Name\"\n[Layer2]\nkeyboard_controls=off\n");s.parse(in);
 assert(!s.flag("ui","CHARACTER_ROSTER_TRANSITIONS"));assert(s.number("UI","roster_fade_ms")==10000);
 assert(s.text("UI","roster_handoff")=="instant");assert(s.text("Misc","survival_stage")=="My # Name");assert(!s.flag("Layer2","keyboard_controls"));
 std::istringstream bad("[UI]\nroster_fade_ms=99\nroster_handoff=bad\ncharacter_roster_transitions=false\ncharacter_roster_transitions=true\nunknown=1\n");s.parse(bad);
 assert(s.number("UI","roster_fade_ms")==10000);assert(s.text("UI","roster_handoff")=="fade");assert(s.flag("UI","character_roster_transitions"));assert(s.diagnostics.size()==4);
 std::cout<<"Settings parsing, bounds, defaults, duplicates and false toggles passed\n";
}

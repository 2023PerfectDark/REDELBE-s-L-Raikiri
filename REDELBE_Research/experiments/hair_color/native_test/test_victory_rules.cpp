#include "victory_rules.h"
#include <cassert>
#include <iostream>
#include <sstream>
int main(){using namespace victoryrules;
 Rule general;general.id="general";general.winner="KAS";general.priority=100;
 Rule special;special.id="vs_ayane";special.winner="KAS";special.opponent="AYA";
 Rule second=special;second.id="vs_ayane_alt";second.weight=3;
 std::vector<Rule> rules{general,special,second};
 assert(choose(rules,"KAS","HON",0)->id=="general");
 assert(choose(rules,"KAS","AYA",0)->id=="vs_ayane");
 for(unsigned i=1;i<4;++i)assert(choose(rules,"KAS","AYA",i)->id=="vs_ayane_alt");
 assert(!choose(rules,"AYA","KAS",0));
 rules[1].enabled=false;rules[2].enabled=false;
 assert(choose(rules,"KAS","AYA",0)->id=="general");
 rules[0].weight=0;assert(!choose(rules,"KAS","AYA",0));
 rules[1].enabled=rules[2].enabled=true;rules[1].priority=1;
 assert(choose(rules,"KAS","AYA",999)->id=="vs_ayane");
 std::istringstream ini("[Intro.Kasumi]\ncharacter=KAS\nopponent=*\nbody=Clips/intro.g1a\nvoice_en=Audio/EN.wav\nvoice_jp=Audio/JP.wav\nvoice_start_en=0.5\n[Victory.Ayane]\ncharacter=KAS\nopponent=AYA\nbody=Clips/win.g1a\n");
 auto parsed=parse(ini);assert(parsed.size()==2);
 assert(relative("Clips/intro.g1a")&&relative("Audio\\JP.wav"));
 for(auto path:{"../escape.g1a","C:/escape.g1a","/escape.g1a","a//b.g1a","a/../b.g1a","\\\\server\\share","a/"})assert(!relative(path));
 assert(choose(parsed,"KAS","HON",0,Phase::Intro)->id=="Kasumi");assert(!choose(parsed,"KAS","HON",0));
 assert(choose(parsed,"KAS","AYA",0)->id=="Ayane");
 parsed[1].opponent="AYA,HON";
 assert(choose(parsed,"KAS","HON",0)->id=="Ayane");
 assert(!choose(parsed,"HON","AYA",0));
 parsed[1].winner="KAS, PHF";parsed[1].opponent="AYA,HON";
 assert(choose(parsed,"PHF","HON",0)->id=="Ayane");assert(!choose(parsed,"RYU","HON",0));
 parsed[1].winner="*";assert(choose(parsed,"RYU","HON",0)->id=="Ayane");
 for(auto list:{"KAS,","KAS,,AYA","*,KAS","KAS,KAS","kas",""})assert(!characterList(list));
 for(auto bad:{"body=../escape.g1a","body=C:/escape.g1a","body=/escape.g1a","body=a//b.g1a","weight=-1","voice_start_en=nan","voice_start_en=2bad","unknown=true","enabled=maybe","character=kas"}){
  std::istringstream input(std::string("[Victory.test]\ncharacter=KAS\nbody=Clips/win.g1a\n")+bad+"\n");bool rejected=false;try{parse(input);}catch(const std::runtime_error&){rejected=true;}assert(rejected);
 }
 std::cout<<"Victory rule specificity, priority, weights, disabled and no-match checks passed\n";
}

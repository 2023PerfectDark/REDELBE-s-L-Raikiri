#pragma once
#include <string>
#include <vector>
#include <cstdint>
#include <limits>
#include <istream>
#include <stdexcept>
#include <cmath>
#include <set>
namespace victoryrules {
enum class Phase {Intro,Victory};
struct Rule {
 Phase phase=Phase::Victory;
 std::string id,winner,opponent="*",body,camera,english,japanese;
 bool enabled=true;
 int priority=0;
 unsigned weight=1;
 float englishStart=0,japaneseStart=0;
};
static bool matches(const std::string& list,const std::string& character){
 if(list=="*")return true;size_t start=0;
 while(start<list.size()){auto end=list.find(',',start);if(end==std::string::npos)end=list.size();auto a=list.find_first_not_of(" \t",start),b=list.find_last_not_of(" \t",end-1);if(a<end&&b>=a&&list.substr(a,b-a+1)==character)return true;start=end+1;}
 return false;
}
// Exact opponent rules outrank general rules. Priority then resolves packs;
// equal-ranked candidates use their weights and a caller-supplied random draw.
static const Rule* choose(const std::vector<Rule>& rules,const std::string& winner,const std::string& opponent,uint64_t draw,Phase phase=Phase::Victory){
 int specificity=-1,priority=std::numeric_limits<int>::min();uint64_t total=0;
 for(const auto& r:rules){
  if(r.phase!=phase||!r.enabled||!r.weight||!matches(r.winner,winner)||!matches(r.opponent,opponent))continue;
  int exact=(r.opponent!="*"?2:0)+(r.winner!="*"?1:0);
  if(exact>specificity||(exact==specificity&&r.priority>priority)){specificity=exact;priority=r.priority;total=0;}
  if(exact==specificity&&r.priority==priority)total+=r.weight;
 }
 if(!total)return nullptr;draw%=total;
 for(const auto& r:rules){
  if(r.phase!=phase||!r.enabled||!r.weight||!matches(r.winner,winner)||!matches(r.opponent,opponent)||((r.opponent!="*"?2:0)+(r.winner!="*"?1:0))!=specificity||r.priority!=priority)continue;
  if(draw<r.weight)return &r;draw-=r.weight;
 }
 return nullptr;
}
static std::string trim(std::string value){auto a=value.find_first_not_of(" \r\n\t"),b=value.find_last_not_of(" \r\n\t");return a==std::string::npos?"":value.substr(a,b-a+1);}
static bool character(const std::string& value){if(value.size()!=3)return false;for(char c:value)if(!(c>='A'&&c<='Z')&&!(c>='0'&&c<='9'))return false;return true;}
static bool characterList(const std::string& value){if(value=="*")return true;size_t start=0;std::set<std::string> seen;
 while(start<value.size()){auto end=value.find(',',start);if(end==std::string::npos)end=value.size();auto token=trim(value.substr(start,end-start));if(!character(token)||!seen.insert(token).second)return false;if(end==value.size())return true;start=end+1;}
 return false;
}
static bool relative(const std::string& value){
 if(value.empty())return true;if(value.front()=='/'||value.front()=='\\'||value.find(':')!=std::string::npos)return false;
 std::string part;for(char c:value){if(c=='/'||c=='\\'){if(part.empty()||part=="."||part=="..")return false;part.clear();}else {if(static_cast<unsigned char>(c)<32)return false;part+=c;}}
 return !part.empty()&&part!="."&&part!="..";
}
// Parsing is independent of installation paths and live game state. A bad pack
// is rejected as a whole; file existence is checked by the eventual runtime.
static std::vector<Rule> parse(std::istream& in){
 std::vector<Rule> out;std::set<std::string> sections,keys;std::string line;unsigned number=0;
 auto fail=[&](){throw std::runtime_error("Invalid interaction INI at line "+std::to_string(number));};
 while(std::getline(in,line)){++number;if(line.size()>4096||number>20000)fail();line=trim(line);if(line.empty()||line[0]==';'||line[0]=='#')continue;
  if(line[0]=='['){if(line.back()!=']'||out.size()>=256)fail();auto name=line.substr(1,line.size()-2);Rule r;
   if(name.rfind("Victory.",0)==0){r.phase=Phase::Victory;r.id=name.substr(8);}else if(name.rfind("Intro.",0)==0){r.phase=Phase::Intro;r.id=name.substr(6);}else fail();
   if(r.id.empty()||!sections.insert(name).second)fail();out.push_back(r);keys.clear();continue;
  }
  auto equals=line.find('=');if(out.empty()||equals==std::string::npos)fail();auto key=trim(line.substr(0,equals)),value=trim(line.substr(equals+1));if(!keys.insert(key).second)fail();auto& r=out.back();
  auto integer=[&](int lo,int hi){size_t used=0;int n=0;try{n=std::stoi(value,&used);}catch(...){fail();}if(used!=value.size()||n<lo||n>hi)fail();return n;};
  auto timing=[&](){size_t used=0;float n=0;try{n=std::stof(value,&used);}catch(...){fail();}if(used!=value.size()||!std::isfinite(n)||n<0||n>120)fail();return n;};
  if(key=="character")r.winner=value;else if(key=="opponent")r.opponent=value;
  else if(key=="body")r.body=value;else if(key=="camera")r.camera=value;
  else if(key=="voice_en")r.english=value;else if(key=="voice_jp")r.japanese=value;
  else if(key=="voice_start_en")r.englishStart=timing();else if(key=="voice_start_jp")r.japaneseStart=timing();
  else if(key=="priority")r.priority=integer(-10000,10000);else if(key=="weight")r.weight=integer(1,10000);
  else if(key=="enabled"){if(value!="true"&&value!="false")fail();r.enabled=value=="true";}else fail();
 }
 for(const auto& r:out)if(!characterList(r.winner)||!characterList(r.opponent)||r.body.empty()||!relative(r.body)||!relative(r.camera)||!relative(r.english)||!relative(r.japanese))fail();
 return out;
}
}

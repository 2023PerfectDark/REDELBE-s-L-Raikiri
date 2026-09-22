
#define NOMINMAX
#include <windows.h>
#include <xinput.h>
#include <string>
#include <fstream>
#include <filesystem>
#include <cassert>
#include <iostream>
static std::wstring gameRoot;
static std::wstring wide(const std::string& s){return std::wstring(s.begin(),s.end());}
static std::string utf8(const std::wstring& s){return std::string(s.begin(),s.end());}
static void log(const std::string&){}
static bool sha256(const std::wstring& path,std::string& result){
 std::ifstream f(path);if(!f)return false;
 result.assign(std::istreambuf_iterator<char>(f),{});return true;
}
#include "birthdays.h"
#include "update_notice.h"
int main(){
 assert(noticescroll::pixelOffset(3000,500,200)==0);
 assert(noticescroll::pixelOffset(4000,500,200)==12);
 assert(noticescroll::pixelOffset(4016,500,200)>12&&noticescroll::pixelOffset(4016,500,200)<13);
 assert(noticescroll::pixelOffset(29000,500,200)==300);
 assert(noticescroll::pixelOffset(31000,500,200)==0);
 assert(noticescroll::pixelOffset(5000,100,200)==0);
 const std::wstring longNotice=L"[Title]\n-one\n-two\n-three\n-four\n-five";
 assert(noticescroll::frame(longNotice,0,1000,2,true)==L"[Title]\n-one\n-two");
 assert(noticescroll::frame(longNotice,5000,1000,2,true)==L"[Title]\n-three\n-four");
 assert(noticescroll::frame(longNotice,6500,1000,2,true)==L"[Title]\n-four\n-five");
 assert(noticescroll::frame(longNotice,9000,1000,2,true)==noticescroll::frame(longNotice,0,1000,2,true));
 assert(noticescroll::frame(longNotice,5000,1000,2,false)==longNotice);
 assert(noticescroll::frame(L"[Title]\n-short",5000,1000,2,true)==L"[Title]\n-short");
 auto dir=std::filesystem::absolute("build/notice_test_"+std::to_string(GetCurrentProcessId()));
 std::filesystem::create_directories(dir/"REDELBE_LR");gameRoot=dir.wstring()+L"\\";
 std::ofstream(dir/"REDELBE_LR/update_info.txt")<<"Test notes";
 using namespace updatenotice;gameVersion=L"game1";
 std::filesystem::create_directories(dir/"REDELBE_LR/BirthdayMessages");
 std::ofstream(dir/"REDELBE_LR/BirthdayMessages/Nyotengu.txt")<<"Congratulations test";
 birthdays::heading=L"Happy Birthday, Nyotengu!";
 birthdays::loadSpecialMessage(11,18);assert(birthdays::specialMessage.empty());
 birthdays::loadSpecialMessage(11,19);assert(birthdays::specialMessage==L"Congratulations test");
 assert(birthdays::heading==L"Congratulations Nyotengu!");
 birthdays::heading.clear();birthdays::loadSpecialMessage(11,19);assert(birthdays::specialMessage.empty());

 {std::istringstream list(R"([Birthdays]
A=02-29
B=02-29
Bad=02-30
Unknown=
)");
 assert(birthdays::matching(list,2,29)==L"Happy Birthday, A & B!");}
 {std::istringstream list(R"([Birthdays]
A=02-29
)");assert(birthdays::matching(list,3,1).empty());}
 {std::istringstream list(R"([Settings]
Enabled=0
[Birthdays]
A=01-01
)");assert(birthdays::matching(list,1,1).empty());}

 assert(colorBrackets(L"Body [Title] tail",false)==L"Body ^00~GREEN~[Title]^00~DEFAULT~ tail");
 assert(colorBrackets(L"[One] and [Two]",true)==L"^00~YELLOW~[One]^00~DEFAULT~ and ^00~YELLOW~[Two]^00~DEFAULT~");
 assert(colorBrackets(L"Unclosed [title",true)==L"Unclosed [title");
 assert(!hidden(false)&&!hidden(true));
 menuAt=GetTickCount64()-2000;assert(input(true)==XINPUT_GAMEPAD_RIGHT_THUMB);assert(!developerPage);
 animation(0xdf867d44,"in");
 assert(replacement(0xdf867d44,L"[Update Info]",13).find(L"Test notes")==0);
 assert(buttons(XINPUT_GAMEPAD_B)==XINPUT_GAMEPAD_A);animation(0xdf867d44,"eff_select");animation(0xdf867d44,"out");assert(developerPage&&!hidden(false));buttons(0); // Back does not save.
 followAt=GetTickCount64();assert(input(true)==XINPUT_GAMEPAD_RIGHT_THUMB);
 animation(0xdf867d44,"in");assert(replacement(0xdf867d44,L"[Update Info]",13).empty());
 buttons(0);buttons(XINPUT_GAMEPAD_A);animation(0xdf867d44,"eff_select");animation(0xdf867d44,"out");assert(hidden(true));
 developerPage=false;animation(0xdf867d44,"in");buttons(0);buttons(XINPUT_GAMEPAD_A);animation(0xdf867d44,"eff_select");animation(0xdf867d44,"out");assert(hidden(false));
 opened=false;pulseUntil=followAt=0;menuAt=GetTickCount64()-2000;assert(input(true)==0); // Restart suppression.
 gameVersion=L"game2";assert(!hidden(false)&&!hidden(true)); // New game build resets both.
 gameVersion=L"game1";std::ofstream(dir/"REDELBE_LR/update_info.txt")<<"New notes";
 assert(!hidden(false)&&hidden(true)); // New REDELBE release resets its own message.
 std::cout<<"Update notice sequence, preserved developer text, dismissal, and update invalidation passed\n";
}

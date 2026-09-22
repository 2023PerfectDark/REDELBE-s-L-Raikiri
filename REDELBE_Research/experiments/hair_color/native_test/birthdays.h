#pragma once
#include <sstream>
namespace birthdays {
static std::wstring heading;
static std::wstring bannerFile;
static std::wstring specialMessage;
static void loadSpecialMessage(unsigned month,unsigned day){
    specialMessage.clear();
    if(month!=11||day!=19||heading.find(L"Nyotengu")==std::wstring::npos)return;
    std::ifstream file(gameRoot+L"REDELBE_LR/BirthdayMessages/Nyotengu.txt",std::ios::binary);
    char buffer[16385];file.read(buffer,sizeof(buffer));
    if(file.gcount()<=0||file.gcount()>16384)return;
    std::string data(buffer,static_cast<size_t>(file.gcount()));
    if(data.size()>=3&&static_cast<unsigned char>(data[0])==239&&static_cast<unsigned char>(data[1])==187&&static_cast<unsigned char>(data[2])==191)data.erase(0,3);
    specialMessage=wide(data);
    if(!specialMessage.empty()&&heading==L"Happy Birthday, Nyotengu!")heading=L"Congratulations Nyotengu!";
}
static bool validDate(unsigned month,unsigned day){
    static const unsigned days[]={0,31,29,31,30,31,30,31,31,30,31,30,31};
    return month>=1&&month<=12&&day>=1&&day<=days[month];
}
static std::wstring matching(std::istream& input,unsigned month,unsigned day){
    std::string line;bool section=false,enabled=true;std::wstring names;
    while(std::getline(input,line)){
        if(line.size()>=3&&static_cast<unsigned char>(line[0])==239&&static_cast<unsigned char>(line[1])==187&&static_cast<unsigned char>(line[2])==191)line.erase(0,3);
        if(!line.empty()&&line.back()==13)line.pop_back();
        if(line.empty()||line[0]==';'||line[0]=='#')continue;
        if(line[0]=='['){section=line=="[Birthdays]";continue;}
        if(!section){if(line=="Enabled=0")enabled=false;continue;}
        auto split=line.find('=');if(split==std::string::npos||split==0||split>80)continue;
        auto date=line.substr(split+1);if(date.size()!=5||date[2]!='-'||date[0]<'0'||date[0]>'9'||date[1]<'0'||date[1]>'9'||date[3]<'0'||date[3]>'9'||date[4]<'0'||date[4]>'9')continue;
        unsigned m=(date[0]-'0')*10+date[1]-'0',d=(date[3]-'0')*10+date[4]-'0';
        if(!validDate(m,d)||m!=month||d!=day)continue;
        if(!names.empty())names+=L" & ";names+=wide(line.substr(0,split));
    }
    return enabled&&!names.empty()?L"Happy Birthday, "+names+L"!":L"";
}
static void load(){
    SYSTEMTIME local{};GetLocalTime(&local); // Sole runtime calendar source; no UTC/server date.
    // Explicit developer preview only; never changes Windows or Steam's clock.
    wchar_t preview[32]{};
    GetPrivateProfileStringW(L"BirthdayPreview",L"Date",L"",preview,32,(gameRoot+L"REDELBE_LR/birthday_preview.ini").c_str());
    unsigned year=0,month=0,day=0;
    if(wcslen(preview)==10&&preview[4]==L'-'&&preview[7]==L'-'&&swscanf_s(preview,L"%4u-%2u-%2u",&year,&month,&day)==3&&year>=2000&&year<=9999&&validDate(month,day)&&!(month==2&&day==29&&year%4!=0)){
        local.wYear=static_cast<WORD>(year);local.wMonth=static_cast<WORD>(month);local.wDay=static_cast<WORD>(day);
        log("BIRTHDAY explicit preview date="+utf8(preview)+" (Windows clock unchanged)");
    }
    std::ifstream file(gameRoot+L"REDELBE_LR/birthdays.ini");
    heading=matching(file,local.wMonth,local.wDay);
    loadSpecialMessage(local.wMonth,local.wDay);
    bannerFile.clear();
    if(local.wMonth==9&&local.wDay==20&&heading.find(L"Momiji")!=std::wstring::npos)bannerFile=L"Momiji.jpg";
    if(local.wMonth==10&&local.wDay==4&&heading.find(L"Mila")!=std::wstring::npos)bannerFile=L"Mila.jpg";
    log("BIRTHDAY effective calendar date="+std::to_string(local.wMonth)+"-"+std::to_string(local.wDay)+(heading.empty()?" no birthday":" matched"));
}
}


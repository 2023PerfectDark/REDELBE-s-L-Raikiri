#pragma once
#include <string>
#include <map>
#include <vector>
#include <istream>
#include <algorithm>
#include <cctype>
#include "config_entries.h"
namespace userconfig {
inline std::string trim(std::string s) {
    auto a=s.find_first_not_of(" \t\r\n");if(a==std::string::npos)return {};
    return s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);
}
inline std::string lower(std::string s){for(char& c:s)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));return s;}
inline std::string id(const std::string& section,const std::string& key){return lower(section)+"."+lower(key);}
class Settings {
    std::map<std::string,std::string> values;
    std::map<std::string,bool> present;
public:
    std::vector<std::string> diagnostics;
    Settings(){reset();}
    void reset(){values.clear();present.clear();diagnostics.clear();for(const auto& e:configEntries)values[id(e.section,e.key)]=e.value;}
    bool has(const std::string& section,const std::string& key)const{return present.count(id(section,key))!=0;}
    std::string text(const std::string& section,const std::string& key)const{auto it=values.find(id(section,key));return it==values.end()?"":it->second;}
    bool flag(const std::string& section,const std::string& key)const{return text(section,key)=="true";}
    unsigned number(const std::string& section,const std::string& key)const{return static_cast<unsigned>(std::stoul(text(section,key)));}
    void parse(std::istream& input) {
        reset();std::string line,section;unsigned lineNumber=0;
        while(std::getline(input,line)) {
            ++lineNumber;if(lineNumber==1&&line.compare(0,3,"\xef\xbb\xbf")==0)line.erase(0,3);
            if(line.size()>8192){diagnostics.push_back("Line too long: "+std::to_string(lineNumber));continue;}
            bool quoted=false;
            for(size_t i=0;i<line.size();++i){if(line[i]=='"')quoted=!quoted;
                if(!quoted&&(line[i]==';'||line[i]=='#')&&(i==0||line[i-1]==' '||line[i-1]=='\t')){line.resize(i);break;}}
            line=trim(line);if(line.empty())continue;
            if(line.front()=='['&&line.back()==']'){section=trim(line.substr(1,line.size()-2));continue;}
            auto equal=line.find('=');if(equal==std::string::npos){diagnostics.push_back("Malformed line "+std::to_string(lineNumber));continue;}
            auto key=trim(line.substr(0,equal)),value=trim(line.substr(equal+1));auto name=id(section,key);
            if(value.size()>=2&&value.front()=='"'&&value.back()=='"')value=value.substr(1,value.size()-2);
            const ConfigEntry* entry=nullptr;for(const auto& e:configEntries)if(id(e.section,e.key)==name){entry=&e;break;}
            if(!entry){diagnostics.push_back("Unknown option ignored: "+name);continue;}
            if(present.count(name))diagnostics.push_back("Duplicate option; last value wins: "+name);
            present[name]=true;bool valid=true;std::string type=entry->type;
            if(type=="boolean") {
                value=lower(value);
                if(value=="1"||value=="yes"||value=="on")value="true";
                if(value=="0"||value=="no"||value=="off")value="false";
                valid=value=="true"||value=="false";
            } else if(type=="integer") {
                try{size_t used=0;int n=std::stoi(value,&used);valid=used==value.size()&&n>=entry->minimum&&n<=entry->maximum;if(valid)value=std::to_string(n);}catch(...){valid=false;}
            } else if(type=="enum") {
                value=lower(value);valid=(std::string("|")+entry->choices+"|").find("|"+value+"|")!=std::string::npos&&!value.empty();
            } else valid=value.size()<=entry->maxLength;
            if(valid)values[name]=value;
            else {values[name]=entry->value;diagnostics.push_back("Invalid value; using default: "+name);}
        }
    }
};
static Settings current;
}

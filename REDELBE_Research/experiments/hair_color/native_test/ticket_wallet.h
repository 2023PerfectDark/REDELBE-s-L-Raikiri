#pragma once
#include <cstdint>
#include <set>
#include <string>
#include <sstream>
#include <functional>
#include <utility>

// Local mod currency. No purchase, platform entitlement or game-save fields.
namespace tickets {
struct State {
    uint32_t balance=0;
    std::set<std::string> unlocks;
};
constexpr uint32_t maximumBalance=1000000;
inline bool validKey(const std::string& key) {
    return !key.empty() && key.size()<=160 &&
        key.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")==std::string::npos;
}
inline std::string encode(const State& state) {
    std::ostringstream out;
    out<<"REDELBE_LOCAL_TICKETS 1\n"<<state.balance<<'\n';
    for(const auto& key:state.unlocks)out<<key<<'\n';
    return out.str();
}
inline bool decode(const std::string& data,State& result) {
    if(data.size()>1024*1024)return false;
    std::string normalized;normalized.reserve(data.size());
    for(size_t i=0;i<data.size();++i){
        if(data[i]=='\r'&&i+1<data.size()&&data[i+1]=='\n')continue;
        normalized+=data[i];
    }
    std::istringstream in(normalized);std::string line;State next;
    if(!std::getline(in,line)||line!="REDELBE_LOCAL_TICKETS 1")return false;
    if(!std::getline(in,line)||line.empty()||line.find_first_not_of("0123456789")!=std::string::npos)return false;
    uint64_t value=0;
    for(char digit:line){value=value*10+unsigned(digit-'0');if(value>maximumBalance)return false;}
    next.balance=static_cast<uint32_t>(value);
    while(std::getline(in,line)){
        if(!validKey(line)||!next.unlocks.insert(line).second||next.unlocks.size()>10000)return false;
    }
    result=std::move(next);return true;
}
enum class Purchase { unlocked,alreadyOwned,insufficient,invalid,saveFailed };
class Wallet {
    State state;
    std::function<bool(const std::string&)> persist;
    bool commit(State next) {
        if(!persist(encode(next)))return false;
        state=std::move(next);return true;
    }
public:
    Wallet(State initial,std::function<bool(const std::string&)> save):state(std::move(initial)),persist(std::move(save)){}
    const State& view()const{return state;}
    bool award(uint32_t amount) {
        if(!amount||amount>maximumBalance||state.balance>maximumBalance-amount)return false;
        auto next=state;next.balance+=amount;return commit(std::move(next));
    }
    Purchase unlock(const std::string& key,uint32_t cost) {
        if(!validKey(key)||cost>maximumBalance)return Purchase::invalid;
        if(state.unlocks.count(key))return Purchase::alreadyOwned;
        if(state.balance<cost)return Purchase::insufficient;
        auto next=state;next.balance-=cost;next.unlocks.insert(key);
        return commit(std::move(next))?Purchase::unlocked:Purchase::saveFailed;
    }
};
}

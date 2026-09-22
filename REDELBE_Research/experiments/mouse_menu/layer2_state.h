#pragma once
#include <cstdint>
#include <cstddef>
#include <map>
#include <tuple>
#include <stdexcept>

// Zero is always the normal costume. Entries 1..N are mods for that slot only.
class Layer2Selection {
    std::map<std::tuple<unsigned,uint32_t,uint32_t>, size_t> choices;
public:
    size_t current(unsigned player, uint32_t slot,uint32_t context=0) const {
        auto it=choices.find(std::make_tuple(player,slot,context));
        return it==choices.end()?0:it->second;
    }
    size_t cycle(unsigned player,uint32_t slot,size_t count,int direction,uint32_t context=0) {
        if(player>=2 || (direction!=1 && direction!=-1)) throw std::invalid_argument("selection input");
        auto& value=choices[std::make_tuple(player,slot,context)];
        if(value>count) value=0;
        value=direction>0?(value==count?0:value+1):(value==0?count:value-1);
        return value;
    }
    size_t random(unsigned player,uint32_t slot,size_t count,uint64_t sample,uint32_t context=0) {
        if(player>=2) throw std::invalid_argument("player");
        return choices[std::make_tuple(player,slot,context)]=static_cast<size_t>(sample%(count+1));
    }
};

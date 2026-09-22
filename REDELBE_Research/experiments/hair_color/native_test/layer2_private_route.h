#pragma once
#include <cstdint>
#include <map>

// Only affects model request arguments. UI selections and gameplay character
// identity remain unchanged. An unavailable donor keeps the ordinary mod route.
struct Layer2PrivateRoute {
    uint32_t source[3]{}; // costume, face, hair
    uint32_t work[3]{};
    std::map<uint32_t,uint32_t> aliases;
    uint32_t donorCharacter=0;
    bool enabled=false;
    uint32_t companionSource(uint32_t model) const {
        if(enabled)for(unsigned i=0;i<3;++i)
            if(source[i] && work[i] && model==work[i])return source[i];
        if(enabled)for(const auto& pair:aliases)if(pair.second==model)return pair.first;
        return model;
    }
    bool apply(uint32_t opponentCharacter,uint32_t (&parts)[3]) const {
        if(!enabled || (donorCharacter && donorCharacter==opponentCharacter))return false;
        bool changed=false;
        for(unsigned i=0;i<3;++i) {
            auto found=aliases.find(parts[i]);
            if(found!=aliases.end()){parts[i]=found->second;changed=true;continue;}
            if(source[i] && work[i] && source[i]==parts[i]) {
                parts[i]=work[i];changed=true;
            }
        }
        return changed;
    }
};

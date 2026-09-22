#pragma once
#include <cstdint>
#include <map>
#include <utility>
struct Layer2ModelSource {
    uintptr_t request=0, resource=0, model=0;
    bool operator==(const Layer2ModelSource& other) const {
        return request==other.request && resource==other.resource && model==other.model;
    }
};
class Layer2ModelSources {
    std::map<std::pair<uintptr_t,unsigned>,Layer2ModelSource> observed;
public:
    bool changed(uintptr_t owner,unsigned part,Layer2ModelSource source) {
        auto key=std::make_pair(owner,part);
        if(!source.request||!source.resource||!source.model){observed.erase(key);return false;}
        auto found=observed.find(key);
        if(found!=observed.end() && found->second==source)return false;
        if(observed.size()>2048)observed.clear();
        observed[key]=source;return true;
    }
};

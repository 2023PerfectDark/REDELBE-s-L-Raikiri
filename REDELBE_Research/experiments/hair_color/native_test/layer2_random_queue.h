#pragma once
#include <array>
#include <deque>
#include <cstdint>
#include <cstddef>

// Random results are metadata until the corresponding character is loaded.
struct Layer2RandomChoice {
    uint8_t character=0;
    uint32_t costume=0,face=0,hair=0;
    size_t choice=0;
};
class Layer2RandomQueue {
    std::array<std::deque<Layer2RandomChoice>,2> queues;
public:
    void clear(){for(auto& q:queues)q.clear();}
    void push(unsigned player,const Layer2RandomChoice& value){
        if(player>=2)return;
        // Corrupt/unsupported flow must not grow metadata without bound.
        auto& q=queues[player];if(q.size()>=64)q.pop_front();q.push_back(value);
    }
    bool consume(uint8_t character,uint32_t costume,uint32_t face,uint32_t hair,
                 unsigned& player,Layer2RandomChoice& result){
        for(unsigned p=0;p<2;++p){
            auto& q=queues[p];
            for(size_t i=0;i<q.size();++i){
                auto v=q[i];
                if(v.character!=character||v.costume!=costume||v.face!=face||v.hair!=hair)continue;
                player=p;result=v;
                // The game can reject earlier generated entries; retain later ones.
                q.erase(q.begin(),q.begin()+i+1);return true;
            }
        }
        return false;
    }
};

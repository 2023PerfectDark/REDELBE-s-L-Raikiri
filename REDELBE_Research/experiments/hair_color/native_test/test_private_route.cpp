#include "layer2_private_route.h"
#include <cassert>
int main() {
    Layer2PrivateRoute r;
    r.enabled=true;r.donorCharacter=9;
    for(unsigned i=0;i<3;++i){r.source[i]=10+i;r.work[i]=20+i;}
    uint32_t hanabi[3]{10,11,12},vanilla[3]{10,11,12};
    assert(r.apply(1,hanabi));assert(hanabi[0]==20&&hanabi[1]==21&&hanabi[2]==22);
    assert(vanilla[0]==10&&vanilla[1]==11&&vanilla[2]==12);
    assert(r.companionSource(20)==10&&r.companionSource(21)==11);
    assert(r.companionSource(10)==10&&r.companionSource(99)==99);
    uint32_t conflict[3]{10,11,12};assert(!r.apply(9,conflict));assert(conflict[0]==10);
    uint32_t otherHair[3]{10,11,88};assert(r.apply(1,otherHair));assert(otherHair[2]==88);
    r.aliases[88]=188;r.aliases[89]=189;
    uint32_t alternate[3]{10,11,88};assert(r.apply(1,alternate));assert(alternate[2]==188);
    assert(r.companionSource(189)==89);
    uint32_t alternate2[3]{10,11,89};assert(r.apply(1,alternate2));assert(alternate2[2]==189);
    r.enabled=false;uint32_t disabled[3]{10,11,12};assert(!r.apply(1,disabled));
    assert(r.companionSource(20)==20);
}

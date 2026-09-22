#include "layer2_crossfade.h"
#include <cassert>
#include <cmath>
int main(){
    Layer2CrossfadeClock f;
    assert(f.incoming(0,350)==1.0f);
    f.begin(100);assert(f.incoming(4100,350)==0.0f&&!f.expired(4100,350));
    f.loaded(4100);assert(f.incoming(4100,350)==0.0f);
    assert(std::abs(f.incoming(4275,350)-0.5f)<0.0001f);
    assert(f.incoming(4450,350)==1.0f&&f.expired(4450,350));
    f.begin(5000);assert(!f.expired(9999,350)&&f.expired(10000,350));
    f.loaded(6000);f.loaded(7000);assert(f.started==6000);
    f.cancel();assert(!f.expired(20000,350)&&f.incoming(20000,350)==1.0f);
    f.begin(0);f.loaded(0);assert(f.incoming(175,350)==0.5f);
    f.begin(100);f.loaded(110);assert(f.incoming(105,350)==0.0f);
}

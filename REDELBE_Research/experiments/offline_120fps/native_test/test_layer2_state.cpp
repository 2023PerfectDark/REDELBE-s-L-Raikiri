#include <cstddef>
#include <cassert>
#include <iostream>
#include "layer2_state.h"
#include "layer2_random_queue.h"
#include "layer2_preview_reload.h"
#include "layer2_model_source.h"
int main() {
    Layer2ModelSources sources;
    assert(sources.changed(1,0,{10,20,30}));
    assert(!sources.changed(1,0,{10,20,30}));
    assert(sources.changed(1,0,{10,20,31})); // Same costume/request, new model.
    assert(!sources.changed(1,0,{10,20,31}));
    assert(sources.changed(2,0,{10,20,31})); // Each owner needs its own rebuild.
    assert(sources.changed(1,1,{10,20,31})); // Face/hair independent of body.
    assert(!sources.changed(1,0,{}));
    assert(sources.changed(1,0,{10,20,31})); // Released/reused addresses still rebuild.
    Layer2PreviewReload reload;
    reload.begin(1000,7);
    assert(!reload.take(1200,7)); // Give native cleanup time to run.
    assert(!reload.take(1400,8)); // Never call a game object from another thread.
    assert(reload.take(1400,7));
    assert(!reload.take(1500,7)); // One replacement request only.
    reload.begin(2000,7);reload.cancel();
    assert(!reload.take(2500,7)); // Costume/character navigation supersedes reload.
    reload.begin(3000,7);assert(reload.take(3001,7,true)); // Complete before menu exit.
    Layer2Selection hair;
    assert(hair.current(0,123,456)==0);
    assert(hair.cycle(0,123,2,1,456)==1);
    assert(hair.current(0,123,789)==0); // Different face, different available head mods.
    assert(hair.current(1,123,456)==0); // Other player stays Vanilla.
    assert(hair.cycle(0,123,2,-1,456)==0);
    assert(hair.cycle(0,123,2,-1,456)==2);
    Layer2Selection s;
    const uint32_t ayane=0xafc8b47d,other=123;
    assert(s.current(0,ayane)==0 && s.current(1,ayane)==0);
    // A full 500-mod traversal includes each mod once, then the normal costume.
    for(size_t i=1;i<=500;++i)assert(s.cycle(0,ayane,500,1)==i);
    assert(s.cycle(0,ayane,500,1)==0);
    assert(s.cycle(0,ayane,500,-1)==500);
    for(size_t i=499;;--i) {assert(s.cycle(0,ayane,500,-1)==i);if(i==0)break;}
    assert(s.current(1,ayane)==0 && s.current(0,other)==0);
    assert(s.cycle(1,ayane,2,1)==1 && s.current(0,ayane)==0);
    assert(s.cycle(0,other,0,1)==0);
    // Random selection affects only the requested player/slot, including vanilla.
    assert(s.random(0,ayane,500,501)==0);
    assert(s.random(0,ayane,500,999)==498);
    assert(s.current(1,ayane)==1 && s.current(0,other)==0);
    Layer2RandomQueue q;unsigned player=99;Layer2RandomChoice out;
    q.push(0,{1,10,11,12,1});q.push(0,{2,20,21,22,2});
    q.push(1,{3,30,31,32,3});
    assert(!q.consume(2,20,999,22,player,out)); // Wrong face cannot consume a future entry.
    assert(q.consume(1,10,11,12,player,out)&&player==0&&out.choice==1);
    assert(q.consume(3,30,31,32,player,out)&&player==1&&out.choice==3);
    assert(q.consume(2,20,21,22,player,out)&&player==0&&out.choice==2);
    assert(!q.consume(2,20,21,22,player,out));
    q.push(0,{1,10,11,12,1});q.push(0,{2,20,21,22,0});
    assert(q.consume(2,20,21,22,player,out)&&out.choice==0); // Game rejected earlier candidate.
    assert(!q.consume(1,10,11,12,player,out));
    q.push(1,{3,30,31,32,1});q.clear();assert(!q.consume(3,30,31,32,player,out));
    std::cout<<"PASS: default, 500-mod forward/back wrap, player/slot isolation, explicit random choices, prefetched queues and rejected candidates\n";
}

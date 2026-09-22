#pragma once
#include "layer2_crossfade.h"

// Included inside namespace l2 after the native request/release declarations.
// Only the first two words own a request; the remaining native callback storage
// is empty. Moving these words prevents request replacement cancelling the old
// model before the new one is ready. Release through LR's own handle cleanup.
struct RetainedPreviewHandle { alignas(8) BYTE data[0x38]{}; };
struct HairFade {
    Request request;
    RetainedPreviewHandle outgoing[2];
    void* oldModels[2]{};
    void* newModels[2]{};
    unsigned draws[2]{};
    unsigned renderCalls=0;
    DWORD thread=0;
    Layer2CrossfadeClock clock;
};
static HairFade hairFades[2];
static std::recursive_mutex fadeMutex;
static thread_local bool startingHairFade=false;
static unsigned hairFadeDuration=350;
static void cancelHairFade(unsigned player) {
    if(player>=2)return;
    HairFade retired;
    {
        std::lock_guard<std::recursive_mutex> guard(fadeMutex);
        auto& f=hairFades[player];if(!f.clock.running)return;
        retired=f;f=HairFade{};
    }
    // Cleanup runs on the preview/input thread, never from the render callback.
    for(auto& handle:retired.outgoing)if(*reinterpret_cast<void**>(handle.data))releaseBody(retired.request.object,handle.data);
    log("LAYER2 HAIR CROSSFADE END P"+std::to_string(player+1)+" old_draws="+
        std::to_string(retired.draws[0])+" new_draws="+std::to_string(retired.draws[1])+" render_calls="+std::to_string(retired.renderCalls));
}
static bool beginHairFade(const Request& req) {
    cancelHairFade(req.player);
    BYTE* owner=static_cast<BYTE*>(req.object)+0x98+req.player*0x2d8;
    HairFade f;f.request=req;f.thread=GetCurrentThreadId();
    for(unsigned part=0;part<2;++part){
        BYTE* handle=owner+0x38*(part+1);
        BYTE* request=*reinterpret_cast<BYTE**>(handle);
        if(!request||!*reinterpret_cast<void**>(request+0x60)||!*reinterpret_cast<void**>(request+0x68))return false;
        f.oldModels[part]=*reinterpret_cast<void**>(request+0x68);
    }
    for(unsigned part=0;part<2;++part){
        BYTE* handle=owner+0x38*(part+1);
        memcpy(f.outgoing[part].data,handle,16);
        // The manager also caches requests independently of the owner handle.
        // Invalidate that entry while retaining its shared ownership.
        (*reinterpret_cast<BYTE**>(handle))[0xc]=1;
        memset(handle,0,16);
    }
    f.clock.begin(GetTickCount64());
    std::lock_guard<std::recursive_mutex> guard(fadeMutex);
    hairFades[req.player]=f;
    log("LAYER2 HAIR CROSSFADE BEGIN P"+std::to_string(req.player+1)+" duration_ms="+std::to_string(hairFadeDuration));
    log("LAYER2 HAIR CROSSFADE OLD models="+std::to_string(reinterpret_cast<uintptr_t>(f.oldModels[0]))+","+std::to_string(reinterpret_cast<uintptr_t>(f.oldModels[1])));
    return true;
}
static void pumpHairFades() {
    for(unsigned player=0;player<2;++player){
        bool done=false;
        {
            std::lock_guard<std::recursive_mutex> guard(fadeMutex);
            auto& f=hairFades[player];
            if(!f.clock.running||f.thread!=GetCurrentThreadId())continue;
            BYTE* owner=static_cast<BYTE*>(f.request.object)+0x98+player*0x2d8;
            bool ready=true;
            for(unsigned part=0;part<2;++part){
                BYTE* request=*reinterpret_cast<BYTE**>(owner+0x38*(part+1));
                void* model=request?*reinterpret_cast<void**>(request+0x68):nullptr;
                bool loaded=request&&*reinterpret_cast<void**>(request+0x60)&&model;
                if(loaded)f.newModels[part]=model;
                else ready=false;
            }
            auto now=GetTickCount64();
            if(ready&&!f.clock.ready){f.clock.loaded(now);log("LAYER2 HAIR CROSSFADE READY P"+std::to_string(player+1)+" models="+std::to_string(reinterpret_cast<uintptr_t>(f.newModels[0]))+","+std::to_string(reinterpret_cast<uintptr_t>(f.newModels[1])));}
            done=f.clock.expired(now,hairFadeDuration);
        }
        if(done)cancelHairFade(player);
    }
}

// Native model render signature: four register arguments and thirteen stack
// arguments, verified from the full function on both saved game builds.
#define LR_RENDER_PARAMS void* model,void* a2,void* a3,void* a4,uintptr_t a5,uintptr_t a6,uintptr_t a7,uintptr_t a8,uintptr_t a9,uintptr_t a10,uintptr_t a11,uintptr_t a12,uintptr_t a13,uintptr_t a14,uintptr_t a15,uintptr_t a16,uintptr_t a17
#define LR_RENDER_ARGS model,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17
using PreviewRenderFn=void(*)(LR_RENDER_PARAMS);
static PreviewRenderFn previewRenderOriginal;
static void previewRenderHook(LR_RENDER_PARAMS) {
    float weight=1.0f;
    {
        std::lock_guard<std::recursive_mutex> guard(fadeMutex);
        for(auto& f:hairFades)if(f.clock.running){
            if(f.renderCalls++<8)log("LAYER2 HAIR CROSSFADE DRAW model="+std::to_string(reinterpret_cast<uintptr_t>(model)));
            float incoming=f.clock.incoming(GetTickCount64(),hairFadeDuration);
            for(unsigned part=0;part<2;++part){
                if(model==f.oldModels[part]){weight=1.0f-incoming;++f.draws[0];}
                if(model==f.newModels[part]){weight=incoming;++f.draws[1];}
            }
        }
    }
    // +a8 is the instance opacity read before LR chooses transparent rendering
    // and uploads shader alpha. Multiplication preserves authored transparency.
    if(weight<1.0f){
        float* opacity=reinterpret_cast<float*>(static_cast<BYTE*>(model)+0xa8);
        float previous=*opacity;
        *opacity=previous*weight;
        previewRenderOriginal(LR_RENDER_ARGS);
        *opacity=previous;
    }else previewRenderOriginal(LR_RENDER_ARGS);
}
#undef LR_RENDER_PARAMS
#undef LR_RENDER_ARGS

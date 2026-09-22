from pathlib import Path
p=Path('prototype/layer2_runtime.h');s=p.read_text();s=s.replace('static thread_local bool forceReload=false;','static thread_local bool forceReload=false;\nstatic thread_local uint32_t preservedBody=0;');s=s.replace('if(forceReload){++reloadCacheMisses[index];return false;}','if(forceReload && (!preservedBody || static_cast<uint32_t>(b)!=preservedBody)){++reloadCacheMisses[index];return false;}');needle='    // Native body request handle, verified in request_character_with_id:';i=s.index(needle);s=s[:i]+'''    if(hairPlayer>=0) {
        // Retain the loaded body and let LR replace face/hair requests through
        // its normal asynchronous transition. No release timer or empty-body gap.
        ReloadScope reload;
        struct PreserveBody {uint32_t previous=preservedBody;PreserveBody(uint32_t slot){preservedBody=slot;}~PreserveBody(){preservedBody=previous;}} preserve(req.costume);
        requestHook(req.object,req.player,req.chara,req.costume,req.face,req.hair,req.color,req.hairColor);
        log("LAYER2 HAIR NATIVE TRANSITION P"+std::to_string(req.player+1)+" body_retained=1 delayed_release=0");
        return;
    }
''' + s[i:];s=s.replace('    if(hairPlayer>=0){releaseBody(req.object,handle+0x38);releaseBody(req.object,handle+0x70);}\n','');p.write_text(s)

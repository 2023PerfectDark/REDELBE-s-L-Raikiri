#pragma once
#include <memory>
#include "ticket_storage.h"
#include "native_coins.h"
namespace tickets {
static std::mutex walletMutex;
static std::unique_ptr<Wallet> wallet;
static bool attempted=false;
static std::atomic<unsigned> rewardAmount{0};
static std::atomic<ULONGLONG> rewardUntil{0};
static bool initialize() {
    if(attempted)return wallet!=nullptr;
    attempted=true;State initial;
    auto path=gameRoot+L"REDELBE_LR\\LocalTickets.dat";
    auto loaded=loadFile(path,initial);
    if(loaded==Load::failed){log("TICKETS ledger unreadable; rewards/purchases disabled, file preserved");return false;}
    wallet=std::make_unique<Wallet>(std::move(initial),[path](const std::string& data){return saveFile(path,data);});
    log("TICKETS local wallet ready");return true;
}
static bool gated(){return userconfig::current.flag("Tickets","enabled")&&userconfig::current.flag("Tickets","hair_color_unlocks");}
static std::string hairKey(uint32_t character,uint32_t hair,unsigned color){
    return "hair."+std::to_string(character)+"."+std::to_string(hair)+"."+std::to_string(color);
}
static uint32_t balance(){
    std::lock_guard<std::mutex> guard(walletMutex);return initialize()?wallet->view().balance:0;
}
static bool owned(uint32_t character,uint32_t hair,unsigned color){
    if(!color)return true;
    std::lock_guard<std::mutex> guard(walletMutex);
    return initialize()&&wallet->view().unlocks.count(hairKey(character,hair,color))!=0;
}
static bool purchaseHair(uint32_t character,uint32_t hair,unsigned color,const std::function<bool()>& saveColor){
    if(!gated()||!color)return saveColor();
    std::lock_guard<std::mutex> guard(walletMutex);if(!initialize())return false;
    auto key=hairKey(character,hair,color);
    if(wallet->view().unlocks.count(key)){
        if(nativecoins::balance()<100){log("COINS hair selection denied: need 100 coins");return false;}
        if(!saveColor())return false;
        return nativecoins::debit(100);
    }
    auto cost=userconfig::current.number("Tickets","hair_color_cost");
    if(wallet->view().balance<cost||!saveColor())return false;
    auto result=wallet->unlock(key,cost);
    if(result==Purchase::unlocked)log("TICKETS hair unlocked; balance="+std::to_string(wallet->view().balance));
    return result==Purchase::unlocked;
}
static void awardWin(){
    if(!userconfig::current.flag("Tickets","enabled"))return;
    std::lock_guard<std::mutex> guard(walletMutex);if(!initialize())return;
    auto amount=userconfig::current.number("Tickets","tickets_per_win");
    if(wallet->award(amount)){rewardAmount=amount;rewardUntil=GetTickCount64()+8000;log("TICKETS offline Versus P1 win +"+std::to_string(amount)+" balance="+std::to_string(wallet->view().balance));}
    else log("TICKETS reward not saved (storage failure or balance cap)");
}
}

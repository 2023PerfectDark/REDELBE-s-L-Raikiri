#include "ticket_wallet.h"
#include "ticket_storage.h"
#include <cassert>
#include <iostream>
#include <mutex>
#include "pattern_parts_state.h"
int main(){
    using namespace tickets;
    std::string disk;bool allow=true;
    Wallet wallet({},[&](const std::string& s){if(!allow)return false;disk=s;return true;});
    assert(wallet.unlock("hair.HON.001.5",5)==Purchase::insufficient);
    assert(wallet.award(5));
    assert(wallet.unlock("hair.HON.001.5",5)==Purchase::unlocked);
    assert(wallet.view().balance==0);
    assert(wallet.unlock("hair.HON.001.5",5)==Purchase::alreadyOwned);
    State restored;assert(decode(disk,restored));assert(restored.unlocks.count("hair.HON.001.5"));
    assert(wallet.award(7));allow=false;
    assert(!wallet.award(1));assert(wallet.view().balance==7);
    assert(wallet.unlock("cosmetic.example",5)==Purchase::saveFailed);
    assert(wallet.view().balance==7&&!wallet.view().unlocks.count("cosmetic.example"));
    assert(!wallet.award(maximumBalance));
    assert(wallet.unlock("bad\nkey",1)==Purchase::invalid);
    auto before=restored;
    assert(!decode("REDELBE_LOCAL_TICKETS 1\n-1\n",restored));
    assert(!decode("REDELBE_LOCAL_TICKETS 1\n1000001\n",restored));
    assert(!decode("REDELBE_LOCAL_TICKETS 1\n0\nx\nx\n",restored));
    assert(restored.balance==before.balance&&restored.unlocks==before.unlocks);
    const std::wstring path=L"build\\ticket_wallet_test_"+std::to_wstring(GetCurrentProcessId())+L".dat";
    assert(loadFile(path,restored)==Load::missing);
    assert(saveFile(path,disk));State roundTrip;
    assert(loadFile(path,roundTrip)==Load::loaded&&roundTrip.balance==7);
    assert(!saveFile(path,"corrupt"));
    assert(loadFile(path,roundTrip)==Load::loaded&&roundTrip.balance==7);
    assert(!saveFile(path+L"\\missing\\wallet.dat",disk));
    assert(DeleteFileW(path.c_str()));
    patternparts::ResultState result;
    result.observe(true,1,2,0,0);
    assert(result.consume(1,0)==1);assert(result.consume(1,0)==0);
    assert(result.consume(1,1)==2);assert(result.consume(1,1)==0);
    result.observe(false,1,2,1,1);assert(result.consume(2,1)==0);
    result.observe(true,1,2,0,0);assert(result.consume(1,0)==1);
    std::cout<<"Ticket wallet transaction and serialization tests passed\n";
}

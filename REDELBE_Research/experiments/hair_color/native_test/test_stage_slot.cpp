#include "stage_slot.h"
#include <cassert>
#include <iostream>
int main() {
    assert(stageinfo::slot("S0801LOS_OBORO")=="S0801LOS_OBORO");
    assert(stageinfo::slot("S0802LOS_OBORO")=="S0802LOS_OBORO");
    assert(stageinfo::slot("S0899LOS_OBORO")=="S0899LOS_OBORO");
    assert(stageinfo::slot("stage_08_99_OBORO")=="S0899LOS_OBORO");
    const char* slots[]={"S0101PIR","S0102PIR","S0201BST","S0301CRM","S0302CRM","S0401CLS","S0501PAS","S0502PAS","S0601LAB","S0701MUS","S0702MUS","S0801LOS","S0802LOS","S0901WAY","S1001KYO","S1101BAM","S1102BAM","S1201PRO","S1301GYM","S1501GRD","S1601ISL","S5001IOR","S5101SHP"};
    for(auto code:slots) {
        std::string texture="stage_";texture+=std::string(code+1,2);texture+="_";texture+=code[4];
        assert(stageinfo::slot(texture)==code);
    }
    assert(stageinfo::caption("stage_13_1")=="Slot: S1301GYM Mod: Vanilla");
    assert(stageinfo::slot("stage_01_2")=="S0102PIR");
    assert(stageinfo::slot("stage_04_1")=="S0401CLS");
    assert(stageinfo::slot("stage_06_1")=="S0601LAB");
    assert(stageinfo::caption("stage_random")=="Slot: Random Vanilla Stage/Modded Stage");
    assert(stageinfo::caption("stage_00_0")=="Slot: Random Vanilla Stage/Modded Stage");
    assert(stageinfo::caption("stage_99_9")=="Slot: Random Vanilla Stage/Modded Stage");
    assert(stageinfo::caption("stage_13_1extra")=="Slot: Random Vanilla Stage/Modded Stage");
    assert(stageinfo::caption("other_texture").empty());
    assert(stageinfo::slot("stage_")=="Unknown");
    assert(stageinfo::slot("stage_1x_1")=="Unknown");
    std::cout<<"Stage slot parsing tests passed\n";
}

#include "stage_slot.h"
#include <cassert>
#include <iostream>
int main() {
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

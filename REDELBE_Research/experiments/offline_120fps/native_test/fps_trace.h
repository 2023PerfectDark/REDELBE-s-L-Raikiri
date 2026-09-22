#pragma once
// Research-only observer. Does not alter FPS, timestep, arguments or return path.
namespace fpstrace {
using SceneFn = void(*)(void*, void*);
static SceneFn original = nullptr;
static std::atomic<unsigned> calls{0};
static BYTE* imageBase = nullptr;
static void observe(void* scene, void* frame) noexcept {
    const unsigned count = ++calls;
    if(count != 1 && count != 120 && count != 600)return;
    try {
        unsigned char data[32]{}; SIZE_T read = 0;
        if(!ReadProcessMemory(GetCurrentProcess(), frame, data, sizeof(data), &read) || read != sizeof(data))return;
        void* stack[12]{};
        const USHORT n = CaptureStackBackTrace(0, 12, stack, nullptr);
        std::ostringstream out;
        out << "FPS TRACE unchanged call=" << count << " scene=" << scene << " frame=" << frame << " bytes=";
        const char* digits="0123456789abcdef";
        for(auto b:data)out << digits[b>>4] << digits[b&15];
        out << " stack=";
        for(USHORT i=0;i<n;++i)out << std::hex << (reinterpret_cast<uintptr_t>(stack[i])-reinterpret_cast<uintptr_t>(imageBase)) << ',';
        log(out.str());
    } catch(...) { /* Diagnostics must not disrupt the game. */ }
}
static void hook(void* scene, void* frame) {
    observe(scene, frame);
    original(scene, frame);
}
static void install() {
    imageBase = reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
    auto nt = reinterpret_cast<IMAGE_NT_HEADERS64*>(imageBase + reinterpret_cast<IMAGE_DOS_HEADER*>(imageBase)->e_lfanew);
    const auto signature=l2::bytes("41 8B 4D 10 85 C9 74 0B 33 D2 B8 3C 00 00 00 F7 F1 EB 05 B8 01 00 00 00 41 89 86 A0 00 00 00");
    const auto prologue=l2::bytes("40 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 E0");
    BYTE* target=nullptr;
    auto section=IMAGE_FIRST_SECTION(nt);
    for(unsigned s=0;s<nt->FileHeader.NumberOfSections;++s) {
        if(!(section[s].Characteristics&IMAGE_SCN_MEM_EXECUTE))continue;
        const size_t begin=section[s].VirtualAddress,end=begin+section[s].Misc.VirtualSize;
        if(end<begin||end>nt->OptionalHeader.SizeOfImage)throw std::runtime_error("FPS trace section bounds invalid");
        for(size_t i=begin+0x4b;i+signature.size()<=end;++i) {
            if(memcmp(imageBase+i,signature.data(),signature.size()))continue;
            BYTE* candidate=imageBase+i-0x4b;
            if(memcmp(candidate,prologue.data(),prologue.size()))continue;
            if(target)throw std::runtime_error("FPS trace pattern ambiguous");
            target=candidate;
        }
    }
    if(!target)throw std::runtime_error("FPS trace scene pattern not found");
    BYTE* trampoline=static_cast<BYTE*>(VirtualAlloc(nullptr,0x1000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    if(!trampoline)throw std::runtime_error("FPS trace allocation failed");
    memcpy(trampoline,prologue.data(),prologue.size());
    l2::absoluteJump(trampoline+prologue.size(),target+prologue.size());
    DWORD previous;
    if(!VirtualProtect(trampoline,0x1000,PAGE_EXECUTE_READ,&previous)) {
        VirtualFree(trampoline,0,MEM_RELEASE);
        throw std::runtime_error("FPS trace protection failed");
    }
    FlushInstructionCache(GetCurrentProcess(),trampoline,0x1000);
    original=reinterpret_cast<SceneFn>(trampoline);
    std::vector<BYTE> patch(prologue.size(),0x90);
    l2::absoluteJump(patch.data(),reinterpret_cast<void*>(hook));
    l2::write(target,patch.data(),patch.size());
    log("FPS TRACE observer installed at RVA="+std::to_string(target-imageBase)+"; native timing unchanged");
}
}

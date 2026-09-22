# Hanabi activation crash — 2026-09-16

User confirms crash after activating Hanabi, not while displaying Vanilla.
Dump: C:/Users/Owner/AppData/Local/CrashDumps/DOA6LR.exe.34044.dmp
Loader log ends after LT selects Hanabi and opens its model, texture and support resources.

Exception 0xc0000409, RIP DOA6LR.exe+0x3688b35. Stack scan contains the native
C++ exception path 0x35ee672, 0x22d804c, 0x22d4ed3, 0x22cc980.
Disassembly confirms 0x22d8030 throws "invalid vector<T> subscript".
Caller 0x22cc97b indexes the float vector at owner+0x1b8 with the current model index.
This is the same failing call site as the earlier Tina Patriot Bikini crash.
Stack scan is not a complete unwound stack; it does not establish the ultimate cause.

Installed ASI still includes the experimental model-default cache invalidation fix;
that fix demonstrably does not prevent this Hanabi failure. No further game changes
made during this diagnosis. Package/resource validation is not in-game compatibility.

Next investigation: capture the failing owner, index, vector length and loaded model
identity; compare initializer output against the model consumed at 0x22cc97b.
Distinguish stale reload state from incompatible legacy model metadata before changing
the loader or porting model assets. Do not bypass the bounds check.

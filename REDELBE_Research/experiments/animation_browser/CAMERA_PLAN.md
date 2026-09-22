# Requested browser camera behavior

F8 in Wardrobe or offline Training must ask before entering. Yes opens the browser; No/Back cancels without starting a motion.

Dedicated camera: select and synchronize the animation-specific camera if a verified matching resource is available. Filename matches are candidates, not runtime proof.
Fallback: frame both P1 and P2 like the fighting camera; expose native spectator movement and zoom controls. Wardrobe currently has only one model, so the Training/scene transition path requires implementation rather than pretending a second fighter exists.

Native photo controls observed on 2026-09-21:
- Left stick: Adjust/Move Camera
- Y + Left stick: Move in/out
- Right stick: Adjust focus
- LT / RT: Tilt
- D-pad: Zoom
- Y + D-pad: Aperture
- Right-stick click: Reset
- RB: Take a photo

List controls and camera controls need an explicit mode switch; current browser uses Y for Replay and D-pad for list navigation. Do not silently reuse those inputs for both.

Confirmation UI implemented, build passes, and installed in main game. DLL SHA256 b2ed533dd08e7aa266826208c9465e7bea84587894e70c8d9c3487f600de39ac. Rollback REDELBE_LR/rollback/animation_confirmation_20260921/dinput8.dll. User confirmed No/Yes works in Wardrobe. Training mode gate, selected-fighter targeting, native camera application, synchronized camera time and camera state restoration are not implemented. Do not enable body substitution in arbitrary matches based only on offline network flag 255.

Read-only camera descriptor scan in live photo mode PID17440 found no heap objects with metadata vtable4c19038 in45seconds. Other derived-type metadata candidates are under inspection. No camera pointer writes performed.

Second45second readonly heap scan of four metadata-vtable candidates returnedzero hits; these are reflection metadata, not established live camera objects. Stop repeating these scans. Need trace a concrete native camera method or proven scene camera owner. Photo control guide was observed; native camera values have not been written.

Static follow-up: SetEyeAt binding3364c90 is a generic placeable look-at path (checks7bc602dd and resolves owner chains), not a proven spectator-camera controller. Camera-specific333af70 resolves two handles, verifies305d9d0, and calls native camera virtual+498 to copy camera state into an approximately3b00-byte temporary (ctor2036350). Do not treat either VM binding as a live camera pointer or install arbitrary setters based on the name alone. Current PID52232/base7ff6c0440000 observed but must refresh before live access.

## Native camera class identified (latest investigation)
Static camera::ApplyMotion at 331c770 calls native virtual +4e0. The native class vtable is 4272448, confirmed by getter +498=3075f30 copying its +2ed0 camera state through 20365b0. Destructor assignment 3064d79 also references this vtable. This replaces the unsuccessful reflection-metadata scan approach.
- +488 CommitChanges = 306bab0; takes camera and manager, locks with 2011b70 and invokes 306bc20.
- +4e0 ApplyMotion = 3065d70; receives camera, manager, resource handle, float time. Resolves resource+20, checks motion virtual+20, clamps time to duration+8, evaluates virtual+30 to a stack sample. Sample bit1 writes position camera+2ea0; bit8 writes quaternion +2eac; bit7 writes float+c, bit8 float+18, bit9 float+1c; projection flags govern remaining fields. Do not guess meanings of scalar values until setter paths are verified.
- +498 state getter = 3075f30. It locks, copies from +2ed0, clears output+3a40, releases lock.
- +4a0 = 30761c0 (not yet decoded).
These are static proofs of class/method roles, not proof of which live instance is the visible camera. No new camera writes or hooks installed. Pending read-only native vtable scan and user opening native photo mode. Existing confirmation build remains installed.

Latest diagnostic installed: DLL SHA256 1d18854ca766a7f385f0d0478027fe24691d5eafa04df22d114d1591f5f44dcc. Rollback REDELBE_LR/rollback/native_camera_trace_20260921/dinput8.dll retains user-confirmed confirmation build. native_camera_trace.enabled enables two bounded pass-through hooks, native state getter and native motion. No camera modifications yet. Max512 records,64 camera/caller pairs,2-second throttle. Build passed existing warnings only. Game closed normally and restarted; user asked to return to offline spectator moving camera and reply ready.

Live read-only scan of prior PID52232 found35 native camera vtable instances. Six250ms samples identified one changing camera 1b85d838e10: position(-16.3779,92.5,399.646), quaternion(0,.999934,0,.0114661); eye matches position. This is candidate active fight camera, not a portable address. All other sampled camera states remained unchanged. The process has since restarted; these pointers MUST NOT be reused. Scripts inspect_native_camera.py and sample_native_cameras.py and captures native_camera_scan.json/native_camera_samples.json save evidence. Dedicated playback/free-camera controls remain unfinished.

Latest live capture: diagnostic hooks resolved and produced real camera motion calls (caller2cde184), unlike old VM traces. PID62520/base7ff6122a0000. Spectator moving camera observed274edb48e10, getter callers3395a88(render camera processing) and34035bb(additional scene/controller processing). User then returned to Kasumi Wardrobe; bounded512-record trace had exhausted, so subsequent read-only snapshots used already captured pointers and revalidated vtables. Wardrobe preview candidate274ed8ea850 changed to position(28.3563,139.4703,227.6214); background candidate274edb8cb80 returned to(-71.1825,123.0815,214.2173). Active-camera association still needs proof; never hardcode these addresses.

Camera motion resource native vtable4257ce8 (actual latest valid capture). Native struct: vtable+0,durationfloat+8,rawG1A pointer+10,flags+18. +18 lowdword80018000: validity bit15, camera count bits16..30 (getter2df6410). Payload really is unmodified _A1G2400! Header+8 blockcount*16 equals filesize; duration+16; +32 prefix block count; camera table starts16*(prefixCount+2), track offset signedint at table+8+index*8 times16 relative table. Track types101/102. Type102 has9 channels(type1018). Each channel(count,offset) at track+4+channel*8. Coefficient arrays at track+offset*16, count segments of4float each. Time array at track+(offset+count)*16. Native scalar evaluator2df91b0 binary-searches times then cubic ((a*t+b)*t+c)*t+d using normalized segment time. Need validate all ranges, finite coefficients and strictly increasing times before passing owned file to native evaluator.
Native camera evaluate2dfbaf0 virtual+30 accepts native,index,float time,output. Outputs position and quaternion; source channels0..2 position,3..5 target,6/7/8 camera scalars (meaning not fully verified). Builds quaternion via f89120,86e530. NativeApplyMotion3065d70 consumes these outputs safely under native lock. No dedicated playback or free-camera writes have been implemented yet.
New scripts inspect_native_camera_motion.py (payload+10), inspect_camera_owners.py. Captures native_camera_motion_objects.json, native_camera_samples.json; Kasumi camera test1616bytes in kasumi_camera_test.g1a extracted locally only, not distributable. Camera+6910 is property storage, not a name/owner handle; read showed empty lists on most fixed cameras. Do not treat it as resource ID.

2026-09-21 fallback correction: user confirmed dedicated winning cameras and C movement work. No-camera branch previously retained Wardrobe baseline. Added fixed level fight-style framing at (0,92.5,400), quaternion (0,1,0,0), native spectator FOV .6195915. C/reset uses this preset for clips without a dedicated camera. This is Wardrobe full-body framing, NOT live two-fighter match tracking. Training remains separate outstanding work. Build/tests passed (265 files, five malformed rejections and full-height framing check). Installed SHA256 4ad39bcf62f30532938687ac7dd8735ab8c74d0ca6721271855797fb78d38789 with timestamped animation_fallback rollback; normal game restart succeeded. Visual confirmation pending.
2026-09-21: User confirmed fallback framing works. Added right-stick/arrow orbit around Wardrobe torso pivot (0,92.5,0); rotates eye and quaternion together, preserves radius, limits pitch near poles. Existing translation, zoom and roll retained. Build and 265 camera validations, malformed-file tests, quarter-turn and radius checks passed. Installed with animation_orbit rollback; visual test pending. This pivot is Wardrobe scene-local, not yet a moving fighter skeleton target.

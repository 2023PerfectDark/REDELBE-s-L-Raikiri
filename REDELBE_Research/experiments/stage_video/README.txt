STAGE VIDEO PREVIEW — EXPERIMENTAL TEST

Use windowed or borderless mode. This first test uses a click-through Windows
video overlay aligned to the native preview pane. Exclusive fullscreen and
game-only recording may not show the overlay. It is not a native renderer hook.

1. Put your Road Rage MP4 at REDELBE_LR\StageVidPreviews\S0901WAY.mp4.
   Use H.264 MP4, preferably 1280x720, 30 fps for this CPU-decoded prototype.
2. Run the installed test game build.
3. The test loader starts the helper automatically on Stage Select. If you stop
   it manually, Start Stage Video Preview Test.cmd starts it again.
4. Select Road Rage. The normal image/name appears first. When the native name
   opacity reaches zero, the clip fades in over 500 ms and loops.
5. Every stage/variant change hides the video and repeats the sequence. Missing
   or unreadable videos leave the normal picture visible. New files are retried
   every second; a game restart is not needed after adding a video.

Other stages use their slot code as the MP4 filename, including separate codes
for each variant. The overlay disappears when the game loses focus or exits.
To stop the helper early, run Stop Stage Video Preview Test.cmd.

Status: decoder tests/build checked; live video appearance awaits an actual clip.
The existing public release package is unchanged.

RANDOM SLOT: Put any MP4 filenames in StageVidPreviews\Random Vanilla Stage-Modded Stage.
Entering Random chooses a video from that folder. At its end another is chosen,
avoiding an immediate repeat when at least two files are available. A single file
repeats. An empty folder keeps the normal picture. Audio/music options apply.

Audio options are in REDELBE_LR\REDELBE.ini, [StageVideoPreviews].
audio_enabled=true plays audio when a playable track exists; audio_volume=100
sets preview volume. game_music_mode=lower reduces only game music while preview
audio is playing; game_music_percent=20 keeps 20% of its normal level. Set mode
to mute for no game music during audible previews, or unchanged to leave it alone.
Preview exit, focus loss or helper timeout restores the prior music level.
The loader does not write the game's saved audio preferences. Restart after edits.

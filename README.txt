Crash Twinsanity (PAL, SLES-52568 v1.01) - CrashModded
=======================================================

Quick start
-----------
1. Put your original PAL ISO in this folder (any file name - it is recognised by its PCSX2 CRC 1510E1D1).
2. Double-click "Build Modded ISO.bat". It builds "<name> [Modded].iso" next to it and then installs the
   matching PCSX2 settings (step "Apply" below). Needs Python, the .NET SDK and Visual Studio's MSBuild
   (only the first time, to build the level tool). The original ISO is never modified.
3. Boot the [Modded] ISO in PCSX2 and press Alt+Enter for fullscreen.

Built into the [Modded] ISO (tools\build_mod.py)
--------------------------------------------------
1. 480p Mode / 60Hz  (by PeterDelta)               mod\elf_patches.txt
   Changes 3 instructions in sceGsResetGraph so the game outputs 480p progressive at 60Hz instead of
   50Hz PAL interlaced. FMVs play ~10% fast (known side effect, gameplay speed is fine).
   Real PS2: needs a 480p-capable connection (component cables or HDMI adapter); over SCART/composite
   to a PAL TV you'll get no picture - use the original ISO there.

2. Cutscene skip - hold Triangle                   mod\elf_patches.txt + mod\levels\*.ops
   The developers left the skip logic in the level scripts but stubbed script condition 572
   ("CutsceneSkipped") to always say no. The executable patch re-implements it as "player holds
   Triangle" (reusing the game's own Triangle check), which brings back every cutscene whose skip
   rule was still wired in (Aku Aku training, Totem Hokum, Dingodile, Uka Uka, Henchmania, ...).
   For others the developers had also moved the skip rule to an unreachable state; mod\levels\*.ops
   puts it back, each tested with the rig (full vs skipped: same end state, gameplay back sooner):
     beach (Aku Aku crate), beach training, angry skunk, Iceberg Lab, Slip Slide Icecapades,
     Academy hub, Rooftop Rampage, treasure room.
   Small differences after skipping: a few level hints ("Clear a path for Cortex!", "Use (O) to
   crouch") are not shown, and in Iceberg Lab Crash stands a few steps from where the scene ends.
   Deliberately left unskippable: totem falling (skipping it gets Crash killed by the totem chase).
   Still in progress (mod\levels-wip): Classroom Chaos, core intro, Rockslide Rumble, Walrus,
   Psychetron room, dorm room, bell tower, party arena, lab interior.

PCSX2 only (installed by "Apply CrashMod Settings.bat", safe to run any time with PCSX2 closed)
------------------------------------------------------------------------------------------------
3. Widescreen 16:9  (by CRASHARKI)  or  21:9 Ultrawide  (TechieSaru's fix + CRASHARKI's flag)
   PCSX2 patches for the display you have; 21:9 is enabled. Use one, never both. The PAL game also has
   widescreen as a normal in-game option.
4. HD textures  (CRASHARKI's ctwin-tp, github.com/CRASHARKI/ctwin-tp) from downloads\ctwin-tp-main.zip
   -> Documents\PCSX2\textures\SLES-52568\replacements (616 PNGs, English level cards). The optional
   "PlayStation Save Icon" variant is in ...\SLES-52568\optional.
5. Per-game graphics ("PCSX2 settings\SLES-52568 game settings.ini", applied to every CRC in
   "PCSX2 patches"): 6x internal resolution, 16x anisotropic filtering, High blending accuracy,
   CAS sharpening 50%, dithering off (Force 32bit), Stretch aspect, FMVs at 4:3, texture replacements
   on, mipmapping off. If it stutters, lower Internal Resolution to 4x.
   Changing a game's Properties in PCSX2 rewrites its .ini - edit it there or in this file, not both.
6. English BIOS language: the PAL disc uses the console's system language from the BIOS .NVM file;
   initialised .NVM files are switched to English (originals kept as .NVM.bak).

Repository layout
-----------------
mod\                   what the mod changes: executable patches, level script recipes, PCSX2 patch template
tools\build_mod.py     builds the [Modded] ISO from the original
tools\isotools.py      ISO9660 / CRASH.BD+BH archive / executable helpers
tools\twinsdump\       level inspection and editing CLI (uses the Twinsanity Editor library)
tools\rig\             automated test rig: drives an isolated PCSX2 over PINE (setup_test_pcsx2.py creates it)
tools\twinsanity-editor, tools\twinsanity-reversed   upstream projects (git submodules)
Not in git: ISOs, extracted game data, downloads\, tools\pcsx2-test\ (copyrighted or rebuilt).

Not included (and why)
----------------------
- Beyond Twinsanity content mods (AnTime Agony, Lava Caves): new content, not fixes;
  installed with CrateModLoader (https://github.com/TheBetaM/CrateModLoader).

Credits: PeterDelta (github.com/PeterDelta/PCSX2), CRASHARKI (PCSX2/pcsx2_patches,
github.com/CRASHARKI/ctwin-tp), TechieSaru (21:9 fix, gbatemp.net/threads/648804),
Smartkin/NeoKesha and contributors (Twinsanity Editor, twinsanity-reversed).

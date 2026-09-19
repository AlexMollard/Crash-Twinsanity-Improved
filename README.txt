Crash Twinsanity (PAL, SLES-52568 v1.01) - community patches
==============================================================

Files
-----
Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It).iso            original, untouched (PCSX2 CRC 1510E1D1)
Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It) [Modded].iso   480p/60Hz built in (PCSX2 CRC 31046581)
PCSX2 patches\                                                         .pnach files (also installed to Documents\PCSX2\patches)

What's applied
--------------
1. 480p Mode / 60Hz  (by PeterDelta)            -> built into the [Modded] ISO
   Changes 3 instructions in sceGsResetGraph (0x2C24A4/A8/B4) so the game outputs
   480p progressive at 60Hz instead of 50Hz PAL interlaced. Only these 12 bytes differ
   from the original disc.
   - FMVs play ~10% fast (known side effect, gameplay speed is fine).
   - Real PS2: needs a 480p-capable connection (component cables or HDMI adapter).
     Over SCART/composite to a PAL TV you'll get no picture - use the original ISO there.

2. Widescreen 16:9  (by CRASHARKI)               -> PCSX2 patch only
   The PAL game already has widescreen as a normal option (saved to the memory card).
   The patch just forces it on from boot. It isn't built into the ISO so 4:3 TV
   players can still turn it off.

3. 21:9 Ultrawide  (TechieSaru's 21:9 Widescreen Fix + CRASHARKI's flag)  -> PCSX2 patch
   Changes the game's 16:9 aspect constant (1.7778) to 21:9 (2.3333) in 4 places and sets
   PCSX2's output to Stretch. Play fullscreen (Alt+Enter) on the 21:9 monitor.
   Use "Widescreen 16:9" instead on a 16:9 screen - never both at once.

4. HD textures  (CRASHARKI's ctwin-tp, github.com/CRASHARKI/ctwin-tp)
   Installed to Documents\PCSX2\textures\SLES-52568\replacements (616 PNGs, English level cards).
   The optional "PlayStation Save Icon" variant is in ...\SLES-52568\optional - move it into
   replacements (replacing Icons\a66c238000a06db-b0b77ea668c4544e-00001993.png) to use it.

Settings reset? Double-click "Apply CrashMod Settings.bat" (with PCSX2 closed).
It restores the patches, the per-game settings below, the HD textures (from downloads\ctwin-tp-main.zip)
and the English BIOS language. Safe to run any time. The settings it applies live in
"PCSX2 settings\SLES-52568 game settings.ini" - edit that file to change what gets restored.

PCSX2 setup (already done, per game in Documents\PCSX2\gamesettings\SLES-52568_*.ini)
--------------------------------------------------------------------------------------
Patch enabled:   Widescreen 21:9 Ultrawide
Graphics:        6x internal resolution, 16x anisotropic filtering, High blending accuracy,
                 CAS sharpening 50%, FMVs kept at 4:3, texture replacements on, mipmapping off
If it stutters, lower Internal Resolution to 4x (right-click game -> Properties -> Graphics).
Note: changing a game's Properties while it runs rewrites that .ini - edit it there, not both.

Game not in English? The PAL disc uses the console's system language, stored in the BIOS .NVM file.
The SCPH-77004 and SCPH-70004 .NVM files in Documents\PCSX2\bios were set to German and have been
switched to English (originals kept as .NVM.bak). For another BIOS, use System -> Start BIOS ->
System Configuration -> Language.

Not included (and why)
----------------------
- Beyond Twinsanity content mods (AnTime Agony, Lava Caves): new content, not fixes;
  installed with CrateModLoader (https://github.com/TheBetaM/CrateModLoader).

Credits: PeterDelta (github.com/PeterDelta/PCSX2), CRASHARKI (PCSX2/pcsx2_patches,
github.com/CRASHARKI/ctwin-tp), TechieSaru (21:9 fix, gbatemp.net/threads/648804).

@echo off
rem Builds "<original name> [Modded].iso" from the original PAL Crash Twinsanity ISO in this folder,
rem then installs the matching PCSX2 settings (patches, graphics, HD textures, English BIOS).
cd /d "%~dp0"
python tools\build_mod.py %* || goto :failed
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Apply-CrashMod.ps1" -NoPause
pause
exit /b 0
:failed
echo.
echo Build failed - see the message above.
pause
exit /b 1

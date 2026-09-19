@echo off
rem Re-applies the Crash Twinsanity mod setup to PCSX2 (patches, per-game settings, HD textures, English BIOS).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Apply-CrashMod.ps1" %*

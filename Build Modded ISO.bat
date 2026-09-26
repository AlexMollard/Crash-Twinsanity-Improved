@echo off
rem Builds "<original name> [Modded].iso" from the original PAL Crash Twinsanity ISO in this folder,
rem then installs the matching PCSX2 settings (patches, graphics, HD textures, English BIOS).
cd /d "%~dp0"

rem Find Python 3: "python" on PATH (not the Microsoft Store stub), else the "py" launcher.
set "PY="
python -c "import sys; sys.exit(sys.version_info[0] < 3)" >nul 2>&1 && set "PY=python"
if not defined PY py -3 -c "" >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo Python 3 is not installed. Get it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
    goto :failed
)

echo Checking Python packages...
%PY% -m pip --version >nul 2>&1 || %PY% -m ensurepip --upgrade >nul || goto :failed
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto :failed

where git >nul 2>&1 || (echo Git is not installed. Get it from https://git-scm.com/download/win & goto :failed)
where dotnet >nul 2>&1 || (echo The .NET SDK is not installed. Get it from https://dotnet.microsoft.com/download & goto :failed)

%PY% tools\build_mod.py %* || goto :failed
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Apply-CrashMod.ps1" -NoPause
pause
exit /b 0
:failed
echo.
echo Build failed - see the message above.
pause
exit /b 1

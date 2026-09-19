<#
  Re-applies the Crash Twinsanity (PAL, SLES-52568) mod setup to PCSX2:
    1. patch files       PCSX2 patches\*.pnach            -> <PCSX2>\patches
    2. per-game settings PCSX2 settings\...game settings  -> <PCSX2>\gamesettings\SLES-52568_<CRC>.ini
                         (for every CRC that has a patch file: the original ISO and the current [Modded] build)
    3. HD texture pack   downloads\ctwin-tp-main.zip      -> <PCSX2>\textures\SLES-52568\replacements
                         (reinstalled only if missing or incomplete)
    4. BIOS language     <PCSX2>\bios\*.NVM set to English (only initialised v1.70+ configs,
                         original kept as .NVM.bak)

  Safe to run any number of times. PCSX2 must be closed, because it rewrites these files itself.
  Usage: double-click "Apply CrashMod Settings.bat", or
         powershell -ExecutionPolicy Bypass -File Apply-CrashMod.ps1 [-DataDir <path>] [-NoPause]
#>
param(
    [string]$DataDir = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PCSX2'),
    [switch]$SkipProcessCheck,
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'
$ModDir   = $PSScriptRoot
$Serial   = 'SLES-52568'
$Crcs     = @(Get-ChildItem (Join-Path $PSScriptRoot 'PCSX2 patches') -Filter "$Serial`_*.pnach" |
              ForEach-Object { $_.BaseName.Substring($Serial.Length + 1) })   # original ISO + current [Modded] build
$TexSkip  = @('Level Cards Japanese_Fixed', 'Level Cards Japanese_NonFixed', 'Level Cards Spanish')
$TexAlt   = 'PlayStation Save Icon'             # alternative icon, kept outside replacements
$NvmOff   = 0x2C0                               # OSD config block (15 bytes + checksum), v1.70+ layout

function Step($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "   $msg" -ForegroundColor Green }
function Note($msg) { Write-Host "   $msg" -ForegroundColor Yellow }
function Done($code) { if (-not $NoPause) { Read-Host "`nPress Enter to close" | Out-Null }; exit $code }

try {
    if (-not (Test-Path $DataDir)) { throw "PCSX2 data folder not found: $DataDir (run PCSX2 once first)" }

    if (-not $SkipProcessCheck) {
        $testRig = Join-Path $ModDir 'tools\pcsx2-test'          # the test rig's own PCSX2 never touches these files
        while (Get-Process -Name 'pcsx2-qt', 'pcsx2' -ErrorAction SilentlyContinue | Where-Object { $_.Path -notlike "$testRig\*" }) {
            if ([Console]::IsInputRedirected) { throw 'PCSX2 is running - close it and run this again.' }
            Note 'PCSX2 is running. Close it completely (it overwrites these files), then press Enter.'
            Read-Host | Out-Null
        }
    }
    Write-Host "PCSX2 data folder: $DataDir"

    Step 'Patch files'
    $patchDir = Join-Path $DataDir 'patches'
    New-Item -ItemType Directory -Force $patchDir | Out-Null
    foreach ($crc in $Crcs) {
        $name = "${Serial}_$crc.pnach"
        Copy-Item (Join-Path $ModDir "PCSX2 patches\$name") (Join-Path $patchDir $name) -Force
        Ok "$name"
    }

    Step 'Per-game settings'
    $gsDir = Join-Path $DataDir 'gamesettings'
    New-Item -ItemType Directory -Force $gsDir | Out-Null
    $template = Join-Path $ModDir "PCSX2 settings\$Serial game settings.ini"
    foreach ($crc in $Crcs) {
        $dest = Join-Path $gsDir "${Serial}_$crc.ini"
        Copy-Item $template $dest -Force
        Ok "${Serial}_$crc.ini"
    }

    Step 'HD texture pack'
    $zipPath = Join-Path $ModDir 'downloads\ctwin-tp-main.zip'
    $texRoot = Join-Path $DataDir "textures\$Serial"
    $repl    = Join-Path $texRoot 'replacements'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        # keep: PNGs not in a skipped language folder
        $entries = @($zip.Entries | Where-Object {
            $full = $_.FullName
            $_.Name -like '*.png' -and -not ($TexSkip | Where-Object { $full -like "*/$_/*" })
        })
        $installed = 0
        if (Test-Path $repl) { $installed = @(Get-ChildItem $repl -Recurse -Filter *.png).Count }
        $expected = @($entries | Where-Object { $_.FullName -notlike "*/$TexAlt/*" }).Count
        if ($installed -ge $expected) {
            Ok "already installed ($installed textures)"
        } else {
            Note "found $installed of $expected textures - reinstalling"
            foreach ($e in $entries) {
                $rel = $e.FullName.Substring($e.FullName.IndexOf('/') + 1)      # strip 'ctwin-tp-main/'
                $base = if ($rel -like "$TexAlt/*") { Join-Path $texRoot 'optional' } else { $repl }
                $out = Join-Path $base ($rel -replace '/', '\')
                New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
                [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, $out, $true)
            }
            Ok "installed $(@(Get-ChildItem $repl -Recurse -Filter *.png).Count) textures"
        }
    } finally { $zip.Dispose() }

    Step 'BIOS language (English)'
    $biosDir = Join-Path $DataDir 'bios'
    $nvms = @(Get-ChildItem $biosDir -Filter *.nvm -ErrorAction SilentlyContinue)
    if (-not $nvms) { Note 'no .NVM files found - nothing to do' }
    foreach ($f in $nvms) {
        $b = [System.IO.File]::ReadAllBytes($f.FullName)
        if ($b.Length -lt $NvmOff + 16) { Note "$($f.Name): too small, skipped"; continue }
        $sum = 0; for ($i = 0; $i -lt 15; $i++) { $sum += $b[$NvmOff + $i] }
        $ver = $b[$NvmOff + 1] -shr 5; $lang = $b[$NvmOff + 1] -band 0x1F
        $blank = ($b[$NvmOff..($NvmOff + 15)] | Where-Object { $_ -ne 0 }).Count -eq 0
        if ($blank -or ($sum -band 0xFF) -ne $b[$NvmOff + 15] -or $ver -lt 1 -or $ver -gt 2) {
            Note "$($f.Name): no initialised settings block, skipped (set language in the BIOS menu if needed)"
            continue
        }
        if ($lang -eq 1) { Ok "$($f.Name): already English"; continue }
        $bak = "$($f.FullName).bak"
        if (-not (Test-Path $bak)) { Copy-Item $f.FullName $bak }
        $b[$NvmOff + 1] = [byte](($ver -shl 5) -bor 1)
        $sum = 0; for ($i = 0; $i -lt 15; $i++) { $sum += $b[$NvmOff + $i] }
        $b[$NvmOff + 15] = [byte]($sum -band 0xFF)
        [System.IO.File]::WriteAllBytes($f.FullName, $b)
        Ok "$($f.Name): language $lang -> 1 (English), backup at $(Split-Path $bak -Leaf)"
    }

    Write-Host "`nAll done. Boot the [Modded] ISO and press Alt+Enter for fullscreen." -ForegroundColor Green
    Done 0
}
catch {
    Write-Host "`nERROR: $($_.Exception.Message)" -ForegroundColor Red
    Done 1
}

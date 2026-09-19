"""Creates the isolated portable PCSX2 used by the test rig (tools/pcsx2-test).

  python setup_test_pcsx2.py [--pcsx2 DIR] [--userdata DIR]

Copies the PCSX2 program folder, makes it portable, copies the SCPH-77004 BIOS (with its English .NVM) from the
user's PCSX2 data folder, and derives inis/PCSX2.ini from the user's config with test-rig overrides (PINE on
port 28012, separate game window, muted, uncompressed save states so rig.py can read RAM dumps,
fast CDVD so warps and level loads don't wait on emulated disc reads).
The user's own PCSX2 install and settings are only read, never modified."""
import argparse, glob, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.abspath(os.path.join(HERE, "..", "pcsx2-test"))
OVERRIDES = {
    ("UI", "ConfirmShutdown"): "false", ("UI", "RenderToSeparateWindow"): "true", ("UI", "HideMainWindowWhenRunning"): "true",
    ("UI", "InhibitScreensaver"): "false", ("UI", "PauseOnFocusLoss"): "false", ("UI", "StartFullscreen"): "false",
    ("EmuCore", "EnablePINE"): "true", ("EmuCore", "PINESlot"): "28012", ("EmuCore", "EnableFastBoot"): "true",
    ("EmuCore", "InhibitScreensaver"): "false", ("EmuCore", "SavestateCompressionType"): "0",
    ("EmuCore/Speedhacks", "fastCDVD"): "true",          # test instance only: level loads ~instant
    ("SPU2/Output", "StandardVolume"): "0", ("Achievements", "Enabled"): "false",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcsx2", default=os.path.expanduser(r"~\Downloads\pcsx2-v2.9.65-windows-x64-Qt"))
    ap.add_argument("--userdata", default=os.path.join(os.path.expanduser("~"), "Documents", "PCSX2"))
    o = ap.parse_args()
    if os.path.exists(TEST): raise SystemExit(f"{TEST} already exists - delete it first to recreate")
    shutil.copytree(o.pcsx2, TEST)
    open(os.path.join(TEST, "portable.ini"), "w").close()
    for d in ("inis", "bios", "patches", "gamesettings"): os.makedirs(os.path.join(TEST, d), exist_ok=True)
    for f in glob.glob(os.path.join(o.userdata, "bios", "SCPH-77004_BIOS_V15_EUR_220.*")):
        if not f.endswith(".bak"): shutil.copy2(f, os.path.join(TEST, "bios"))
    out, sec, seen = [], None, set()
    for line in open(os.path.join(o.userdata, "inis", "PCSX2.ini"), encoding="utf-8").read().splitlines():
        m = re.match(r"\[(.+)\]$", line)
        if m: sec = m.group(1)
        key = line.split("=", 1)[0].strip() if "=" in line else None
        if sec == "GameList" and key: continue                    # the test instance doesn't scan game folders
        if (sec, key) in OVERRIDES: line = f"{key} = {OVERRIDES[(sec, key)]}"; seen.add((sec, key))
        out.append(line)
    missing = set(OVERRIDES) - seen
    if missing: raise SystemExit(f"settings not found in the user's PCSX2.ini: {missing}")
    open(os.path.join(TEST, "inis", "PCSX2.ini"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("test PCSX2 ready at", TEST)

if __name__ == "__main__":
    main()

"""Rebuilds the test ISO and the level state library from a fresh boot (save states embed the archive's file
table, so states made from an older build must not be used once file sizes change).

  python rebuild.py [--include DIR ...] [--levels NAME ...]
levels.txt lines: NAME LEVELPATH [cortex]  ('cortex': arrive as Cortex, via make_cortex_state.py)"""
import os, subprocess, sys, time, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); import rig
args = sys.argv[1:]; inc = []; only = []
while args:
    a = args.pop(0)
    if a == "--include": inc += ["--include", os.path.join(ROOT, args.pop(0))]
    elif a == "--levels": only, args = args, []
rig.stop(); time.sleep(2)
subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_mod.py"), "--out", os.path.join(HERE, "test.iso"), "--no-pcsx2-files", *inc], check=True)
rig.start("Levels\Earth\Hub\Beach", "test", "1")
rig.until(os.path.join(HERE, "ref", "main_menu.png"), "start", 2.5, 150, 25)
time.sleep(2); rig.run(["press", "cross", "--frames", "6"]); time.sleep(3)
rig.until(os.path.join(HERE, "ref", "save_select.png"), None, 1, 15)
rig.run(["press", "up", "--frames", "6"]); time.sleep(1); rig.run(["press", "cross", "--frames", "6"]); time.sleep(8)
rig.run(["press", "cross", "--frames", "10"]); time.sleep(6)
rig.until(os.path.join(HERE, "ref", "autosave_disabled.png"), None, 1, 40)
rig.run(["press", "cross", "--frames", "6"]); time.sleep(4)
p = rig.Pine(); rig.Pine().save(8); time.sleep(2)
import shutil; os.makedirs(rig.STATES_DIR, exist_ok=True)
for old in glob.glob(os.path.join(rig.STATES_DIR, "*.p2s")): os.remove(old)   # states embed the old archive file table
shutil.copyfile(rig.slot_file(8), os.path.join(rig.STATES_DIR, "base.p2s"))
print("fresh base state saved", flush=True)
cortex = []
for line in open(os.path.join(HERE, "levels.txt"), encoding="utf-8"):
    s = line.split("#", 1)[0].split()
    if len(s) < 2 or (only and s[0] not in only): continue
    if s[2:3] == ["cortex"]: cortex.append(s); continue      # Cortex levels: made last, they reboot the emulator
    t0 = time.time()
    try:
        rig.level("base"); rig.level(s[0], s[1], fresh=True); print(f"{s[0]}: ok ({time.time() - t0:.0f}s)", flush=True)
    except SystemExit as e:
        print(f"{s[0]}: FAILED {e}", flush=True); rig.pine_reset()
for s in cortex:
    r = subprocess.run([sys.executable, os.path.join(HERE, "make_cortex_state.py"), s[0], s[1]], capture_output=True, text=True)
    print(f"{s[0]}: {'ok' if r.returncode == 0 else 'FAILED ' + (r.stdout + r.stderr).strip().splitlines()[-1]}", flush=True)

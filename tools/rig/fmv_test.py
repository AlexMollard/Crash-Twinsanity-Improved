"""Pre-rendered movie skip test: boots the test ISO fresh, warps to LEVELPATH, teleports onto the movie's trigger,
optionally holds Triangle, then reports when the player has control again, where, and the game-flow state. A fresh
boot matters: save states restore RAM, so they would undo the executable patch under test.

  python fmv_test.py LEVELPATH X Y Z [hold]
  python fmv_test.py Levels\Ice\Hub\labint -14.34 -2.85 -10.33 hold"""
import contextlib, io, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig
OUT = os.path.join(HERE, "results")

path, x, y, z = sys.argv[1], *[float(v) for v in sys.argv[2:5]]
hold = "hold" in sys.argv
tag = "skip" if hold else "full"
os.makedirs(OUT, exist_ok=True)
B = chr(92)
rig.stop(); time.sleep(2)
rig.start(B.join(["Levels", "Earth", "Hub", "Beach"]), "test", "1")
rig.until(os.path.join(HERE, "ref", "main_menu.png"), "start", 2.5, 150, 25)
time.sleep(2); rig.run(["press", "cross", "--frames", "6"]); time.sleep(3)
rig.until(os.path.join(HERE, "ref", "save_select.png"), None, 1, 15)
rig.run(["press", "up", "--frames", "6"]); time.sleep(1); rig.run(["press", "cross", "--frames", "6"]); time.sleep(8)
rig.run(["press", "cross", "--frames", "10"]); time.sleep(6)
rig.until(os.path.join(HERE, "ref", "autosave_disabled.png"), None, 1, 40)
rig.run(["press", "cross", "--frames", "6"]); time.sleep(4)
with contextlib.redirect_stdout(io.StringIO()): rig.level("_fmvtest", path, fresh=True)
p = rig.Pine()

def controllable():
    a = rig.pos(p); rig.set_pad(p, (), 0, -1); time.sleep(0.2); rig.set_pad(p); b = rig.pos(p)
    return math.dist(a, b) > 0.05

rig.teleport(x, y + 1.0, z)
t0 = time.time()
while not rig.in_cutscene() and time.time() - t0 < 15: time.sleep(0.2)
if not rig.in_cutscene(): raise SystemExit("NOT TRIGGERED")
ts = time.time()
if hold: rig.set_pad(p, ("triangle",))
while time.time() - ts < 120:
    if not rig.in_cutscene() and (hold or controllable()): break
    time.sleep(0.2)
if hold:
    rig.set_pad(p)
    while time.time() - ts < 120 and not controllable(): time.sleep(0.2)
secs = round(time.time() - ts, 1)
time.sleep(2)
rig.screenshot(os.path.join(OUT, f"fmv_{tag}_end.png"))
print(f"{tag}: control after {secs}s at {[round(v, 2) for v in rig.pos(p)]}, flow {rig.flow_state(p)}, "
      f"cutscene again {rig.in_cutscene()}", flush=True)
try: os.remove(os.path.join(rig.STATES_DIR, "_fmvtest.p2s"))
except OSError: pass

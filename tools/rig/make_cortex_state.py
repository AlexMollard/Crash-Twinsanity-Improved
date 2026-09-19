"""Level states for Cortex levels (Madame Amberly's bell tower, ...). The rig's warp keeps the character you are
playing, and a new game plays as Crash, so this boots test.iso fresh, warps to Classroom Chaos, skips its opening
scene - it hands control to Cortex - then warps to LEVEL and saves states/NAME.p2s.

  python make_cortex_state.py NAME LEVELPATH
  python make_cortex_state.py amberly_cortex Levels\\school\\Madame\\amberly"""
import contextlib, io, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig

name, path = sys.argv[1], sys.argv[2]
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
p = rig.Pine()
with contextlib.redirect_stdout(io.StringIO()): rig.level("_classroom", B.join(["Levels", "school", "Crash", "crgpa08"]), fresh=True)
before = p.r32(rig.PLAYER_CHAR)
rig.teleport(6.60, 3.08, -20.58); t0 = time.time()                   # Classroom Chaos trigger (cutscenes_orphan.txt)
while not rig.in_cutscene() and time.time() - t0 < 10: time.sleep(0.1)
time.sleep(1.0); rig.set_pad(p, ("triangle",)); time.sleep(1.5); rig.set_pad(p)
while rig.in_cutscene() and time.time() - t0 < 40: time.sleep(0.2)
time.sleep(2)
if p.r32(rig.PLAYER_CHAR) == before: raise SystemExit("the classroom skip did not switch to Cortex")
os.remove(os.path.join(rig.STATES_DIR, "_classroom.p2s"))
rig.level(name, path, fresh=True)

"""Skip test for cutscenes that play the moment a level loads (the spawn is inside the trigger, e.g. the walrus chase),
which cutscene_test.py can't start from a level state. Boots test.iso fresh for each run (the game remembers a seen
scene), warps to LEVEL, times the scene from its start until the player has control (skip: hold Triangle after 1 s),
then logs six frames of what follows. 'run' holds the stick toward the camera once control is back.

  python arrival_test.py NAME LEVELPATH OUTDIR [full|skip] [run]
  python arrival_test.py walrus Levels\Ice\HighSeas\gpa10 results full run"""
import sys, os, time, struct, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig, testhooks as th
name, path, out = sys.argv[1], sys.argv[2], os.path.join(HERE, sys.argv[3])
rig.stop(); time.sleep(2)
rig.start(chr(92).join(["Levels", "Earth", "Hub", "Beach"]), "test", "1")
rig.until(os.path.join(HERE, "ref", "main_menu.png"), "start", 2.5, 150, 25)
time.sleep(2); rig.run(["press", "cross", "--frames", "6"]); time.sleep(3)
rig.until(os.path.join(HERE, "ref", "save_select.png"), None, 1, 15)
rig.run(["press", "up", "--frames", "6"]); time.sleep(1); rig.run(["press", "cross", "--frames", "6"]); time.sleep(8)
rig.run(["press", "cross", "--frames", "10"]); time.sleep(6)
rig.until(os.path.join(HERE, "ref", "autosave_disabled.png"), None, 1, 40)
rig.run(["press", "cross", "--frames", "6"]); time.sleep(4)
p = rig.Pine()
def controllable():
    a = rig.pos(p); rig.set_pad(p, (), 0, -1); time.sleep(0.2); rig.set_pad(p); b = rig.pos(p)
    return math.dist(a, b) > 0.05
for mode in ([m for m in sys.argv[4:] if m in ("full", "skip")] or ["full", "skip"]):  # --moveto x,y,z
    raw = path.encode(); buf = raw + b"\0"; buf += b"\0" * (-len(buf) % 4)
    for i in range(0, len(buf), 4): p.w32(th.WARP_STR + i, struct.unpack("<I", buf[i:i + 4])[0])
    p.w32(rig.LEVEL_START_STR, th.WARP_STR); p.w32(rig.LEVEL_START_STR + 4, len(raw)); p.w32(rig.LEVEL_START_STR + 8, 0x100)
    p.w32(rig.CREDITS_DONE_BRANCH, rig.CREDITS_DONE_ALWAYS)
    flow = p.r32(rig.FLOW_PTR); hi = p.r32(flow + 12); p.w32(flow + 12, (hi & ~(0x3F << 12)) | (rig.STATE_CREDITS << 12))
    try:
        t0 = time.time()
        while rig.flow_state(p) not in (rig.STATE_PLAYING, 13) and time.time() - t0 < 120: time.sleep(0.05)
    finally:
        p.w32(rig.CREDITS_DONE_BRANCH, rig.CREDITS_DONE_ORIG)
    t0 = time.time()
    while not rig.in_cutscene() and time.time() - t0 < 10: time.sleep(0.05)
    if not rig.in_cutscene(): print(mode, "NOT TRIGGERED"); continue
    ts = time.time(); rig.screenshot(os.path.join(out, f"{name}_{mode}_start.png"))
    first = p.r32(rig.PLAYER_CHAR)                         # the character in control when the scene starts
    fpos = lambda: [round(rig.fl(p, first + 0xD0 + 4 * k), 1) for k in range(3)]
    if mode == "skip":
        time.sleep(1.0); rig.set_pad(p, ("triangle",)); time.sleep(1.5); rig.set_pad(p)
    while time.time() - ts < 90:
        if not rig.in_cutscene() and controllable(): break
        time.sleep(0.05)
    if "run" in sys.argv:                                  # flee: hold the stick toward the camera
        rig.set_pad(p, (), 0, 1)
    secs = round(time.time() - ts, 1); pos = [round(v, 1) for v in rig.pos(p)]
    for k in range(6):
        rig.screenshot(os.path.join(out, f"{name}_{mode}_after{k}.png")); print("  after", k, "flow", rig.flow_state(p), [round(v, 1) for v in rig.pos(p)], flush=True); time.sleep(0.25)
    rig.set_pad(p)
    if "--moveto" in sys.argv:                             # put the player on a given spot to compare the view
        x, y, z = (float(v) for v in sys.argv[sys.argv.index("--moveto") + 1].split(",")); rig.teleport(x, y + 0.5, z); time.sleep(1.5)
    rig.screenshot(os.path.join(out, f"{name}_{mode}_end.png"))
    other = f", first character at {fpos()}" if p.r32(rig.PLAYER_CHAR) != first else ""
    print(f"{mode}: control after {secs}s at {pos}, flow {rig.flow_state(p)}{other}", flush=True)

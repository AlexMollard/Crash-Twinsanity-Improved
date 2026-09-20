"""Level load benchmark: fresh boot of the test ISO, New Game, then warps to the hub, Classroom Chaos and the hub again,
printing each load time (warp until Crash can move, 0.5 s steps; includes ~1.5 s of the warp's credits path).
A fresh boot matters: save states restore RAM, so they would undo executable patches under test.

  python load_bench.py LABEL [ISO]                    # ISO: test (default), modded, original, re
  RIG_FASTCDVD=true python load_bench.py LABEL        # PCSX2's Fast CDVD (the preset turns it on)
  RIG_PATCH=ADDR=WORD,... python load_bench.py LABEL  # try executable patches from boot"""
import contextlib, io, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig

LEVELS = [("huba", r"Levels\Earth\Hub\huba"), ("crgpa08", r"Levels\school\Crash\crgpa08"), ("huba2", r"Levels\Earth\Hub\huba")]
ISO = sys.argv[2] if len(sys.argv) > 2 else "test"

rig.stop(); time.sleep(2)
rig.start(r"Levels\Earth\Hub\Beach", ISO, "1")
rig.until(os.path.join(HERE, "ref", "main_menu.png"), "start", 2.5, 150, 25)
time.sleep(2); rig.run(["press", "cross", "--frames", "6"]); time.sleep(3)
rig.until(os.path.join(HERE, "ref", "save_select.png"), None, 1, 15)
rig.run(["press", "up", "--frames", "6"]); time.sleep(1); rig.run(["press", "cross", "--frames", "6"]); time.sleep(8)
rig.run(["press", "cross", "--frames", "10"]); time.sleep(6)
rig.until(os.path.join(HERE, "ref", "autosave_disabled.png"), None, 1, 40)
rig.run(["press", "cross", "--frames", "6"]); time.sleep(4)
out = []
for name, path in LEVELS:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): rig.level("bench_" + name, path, fresh=True)
    m = re.search(r"level loaded in ([\d.]+)s", buf.getvalue()); out.append(f"{name} {m.group(1) if m else '?'}s")
print(f'{sys.argv[1] if len(sys.argv) > 1 else ""} [{ISO}]', " | ".join(out), flush=True)

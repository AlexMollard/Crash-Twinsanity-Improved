"""How long does the front end take to answer a button? Boots an ISO, waits out the boot, then times how long
after each press the screen first changes.

  python menu_time.py original|test

Known rough edges, so read the numbers with care:
  - the front end animates constantly, so "has the screen settled" is not a usable signal; only press-to-change is,
    and it needs a threshold above the animation's own frame-to-frame difference (2.5 works)
  - a black boot screen looks perfectly still, so the wait below is a fixed sleep rather than a settle check
  - the two builds boot at different speeds (62 s retail, 44 s modded to the title), so a fixed wait can land in the
    attract demo on one of them and on the title on the other
  - PINE is not up until the game is running; pressing anything before that resets the connection
  - check what you are actually booting. The modded runs here produced no response at all and two PINE resets
    because tools/rig/test.iso had been rebuilt by another session with a different executable, against save
    states made for the old one. Compare isotools.iso_crc(test.iso) with the pnach in "PCSX2 patches" first.

Measured so far: retail PAL, menu navigation takes about 0.82 s from press to any visible response.
"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig

iso = sys.argv[1] if len(sys.argv) > 1 else "test"
WAIT = float(sys.argv[2]) if len(sys.argv) > 2 else 78
B = chr(92)
rig.stop(); time.sleep(2)
rig.start(B.join(["Levels", "Earth", "Hub", "Beach"]), iso, "1")

def frame():
    for _ in range(90):                      # the emulator window does not exist for the first few seconds
        try: return rig.thumb(*rig.grab())
        except SystemExit: time.sleep(1)
    raise SystemExit("no game window")

def step(name, button, thr=2.5):
    before = frame(); t0 = time.time()
    rig.run(["press", button, "--frames", "6"])
    while time.time() - t0 < 20:
        if rig.diff(frame(), before) > thr:
            print(f"  {name:22s} press -> change {time.time() - t0:.2f}s", flush=True); return
        time.sleep(0.05)
    print(f"  {name:22s} no change within 20s", flush=True)

print(f"{iso}: waiting {WAIT:.0f}s for the front end", flush=True)
time.sleep(WAIT)
print(f"{iso}: front-end response", flush=True)
step("title -> main menu", "start")
step("main menu -> saves", "cross")
step("move the highlight", "up")
step("confirm the save", "cross")
rig.screenshot(os.path.join(HERE, "results", f"menu_{iso}.png"))

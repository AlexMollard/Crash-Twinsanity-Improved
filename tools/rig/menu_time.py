"""How long does the front end take to answer a button? Boots an ISO, waits for the title screen, then times how
long after each press the screen first changes.

  python menu_time.py original|modded|test

READ THIS BEFORE TRUSTING A NUMBER FROM HERE. The front end animates constantly, and the animation crosses the 2.5
threshold on its own every 0.71-0.73 s with no input whatsoever. So press-to-change does NOT measure input latency
here: it measures whichever comes first, the response or the next animation frame, and near 0.8 s those are
indistinguishable. An earlier "retail PAL menus answer in about 0.82 s" came from this harness and was retracted -
it was the animation's period. The control below runs first and refuses to report if it fails.

A valid measurement needs a signal that only moves on input: find the menu-selection variable in RAM and time from
press to its change. The same lesson as jump height, which had to come from the player object rather than the screen.

This used to wait a fixed number of seconds for the front end, which was the harness's worst rough edge: the two
builds boot at different speeds, so one fixed wait lands on the title for one build and in the attract demo for the
other, and a press in the attract demo just exits the demo - a big screen change that has nothing to do with menu
latency. It now waits on the game-flow state instead, and steps out of the attract demo before timing anything.

  flow 5  still settling - pressing here does nothing useful
  flow 6  title screen
  flow 7  attract demo (entered after about 10 s of no input)

Check what you are actually booting. A previous set of modded runs produced no response at all and two PINE resets
because tools/rig/test.iso had been rebuilt by another session with a different executable. Compare
isotools.iso_crc() with the pnach in "PCSX2 patches" first; `modded` and `original` are unambiguous.

Measured: retail PAL takes about 0.82 s from press to any visible response.
"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rig

TITLE, ATTRACT = 6, 7
iso = sys.argv[1] if len(sys.argv) > 1 else "test"
B = chr(92)

rig.stop(); time.sleep(2)
rig.start(B.join(["Levels", "Earth", "Hub", "Beach"]), iso, "1")

def frame():
    for _ in range(90):                      # the emulator window does not exist for the first few seconds
        try: return rig.thumb(*rig.grab())
        except SystemExit: time.sleep(1)
    raise SystemExit("no game window")

def flow():
    try: return rig.flow_state(rig.Pine())
    except Exception: rig.pine_reset(); return -1

def wait_for_front_end(timeout=180):
    """Wait for the title screen, stepping out of the attract demo if the boot has already fallen into it."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = flow()
        if st == TITLE:
            return time.time() - t0
        if st == ATTRACT:                     # a press exits the demo; that press is not a menu response
            rig.run(["press", "start", "--frames", "6"]); time.sleep(3)
        time.sleep(1)
    raise SystemExit(f"front end never reached flow {TITLE}")

def step(name, button, thr=2.5):
    st = flow()
    before = frame(); t0 = time.time()
    rig.run(["press", button, "--frames", "6"])
    while time.time() - t0 < 20:
        if rig.diff(frame(), before) > thr:
            print(f"  {name:22s} (flow {st})  press -> change {time.time() - t0:.2f}s", flush=True); return
        time.sleep(0.05)
    print(f"  {name:22s} (flow {st})  no change within 20s", flush=True)

def ambient_control(trials=5, thr=2.5):
    """Time how long the threshold takes to trip with NO input. If that is near the response times below, the
    numbers are the animation rather than the menus, and there is nothing here worth reporting."""
    out = []
    for _ in range(trials):
        before = frame(); t0 = time.time()
        while time.time() - t0 < 20:
            if rig.diff(frame(), before) > thr: out.append(time.time() - t0); break
            time.sleep(0.05)
        else: out.append(None)
    return out

took = wait_for_front_end()
amb = ambient_control()
hits = [t for t in amb if t is not None]
print(f"{iso}: title after {took:.0f}s. Ambient control, no input: "
      f"{['%.2fs' % t for t in hits] if hits else 'never tripped'}", flush=True)
if hits and min(hits) < 3.0:
    print(f"  ABORT: the screen trips the threshold on its own every ~{sum(hits)/len(hits):.2f}s, so any "
          f"press-to-change figure from here is the animation, not the menu. Measure a RAM signal instead.",
          flush=True)
    rig.screenshot(os.path.join(HERE, "results", f"menu_{iso}.png"))
    raise SystemExit(1)
print(f"{iso}: front-end response", flush=True)
step("title -> main menu", "start")
step("main menu -> saves", "cross")
step("move the highlight", "up")
step("confirm the save", "cross")
rig.screenshot(os.path.join(HERE, "results", f"menu_{iso}.png"))

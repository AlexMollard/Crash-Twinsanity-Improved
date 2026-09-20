"""Measure one fixed slide jump, frame-exactly, to compare 50 Hz against 60 Hz.

The community blames the slide-deviation bug - a slide throwing Crash in a direction he was not pointed in - on the
60 Hz update rate rather than on the region, and says slide jumps at 60 Hz are shorter. This mod runs the 50 Hz PAL
game at 60 Hz, so it is the one case that would reintroduce it. This is the harness behind the figures on the
versions page.

Two things had to be right before any number meant anything.

Input. Wall-clock presses cannot be compared across frame rates, because 0.4 s is 20 frames at 50 Hz and 24 at
60 Hz, and they were not repeatable even at one rate - the same scripted press jumped 0 to 3 times out of 4. Every
press here is counted in game frames off the counter at 0x309B68, so both builds get an identical number of updates
of identical input. From a fixed save state the whole trial then replays to three decimals.

Height. The player object's position at +0xD0 is ground-projected: its y does not move at all while Crash is
airborne, so `rig.pos()` shows a flat line through a perfectly good jump. The real fields are +0x284 (height above
ground) and +0x064 (vertical velocity), found by diffing the object through a press.

Run it against a build that is already booted and warped to a level; measure each build from its own cold boot,
because a save state carries the executable and the 50/60 Hz difference is an executable patch.

    python tools/rig/rig.py start --iso original --level Levels\\Earth\\Hub\\huba
    python tools/rig/slidejump.py huba_orig --warp Levels\\Earth\\Hub\\huba
"""
import argparse, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig

FRAME = 0x309B68            # +1 per game frame; 50.00 Hz retail, 59.97 Hz modded
H_OFF = 0x284               # player object: height above ground
VV_OFF = 0x064              # player object: vertical velocity

# The run-up has to be long enough that his heading has settled: in the Earth hub he clips scenery around frames
# 32-56 and a shorter run-up measures that deflection (17 degrees) instead of the jump.
RUN_FRAMES, SLIDE_FRAMES, JUMP_FRAMES, AIR_FRAMES = 80, 12, 14, 90
GROUND = 0.05

def frame(p): return p.r32(FRAME)

def hold(p, obj, buttons, frames, lx, ly, clock=None, sample=False):
    """Set the pad, then wait exactly FRAMES game frames. CLOCK gives samples from separate phases one timebase."""
    rig.set_pad(p, buttons, lx, ly)
    out = []; f0 = last = frame(p)
    while True:
        f = frame(p)
        if f != last:
            last = f
            if sample:
                x, _, z = rig.pos(p)
                out.append((f - (clock if clock is not None else f0), x, z,
                            rig.fl(p, obj + H_OFF), rig.fl(p, obj + VV_OFF), time.time()))
        if f - f0 >= frames: break
    return out

def trial(p, lx=0.0, ly=-1.0):
    """Run up, slide, jump. Returns distance, deviation from the run-up heading, peak height and airtime."""
    obj = p.r32(rig.PLAYER_CHAR)
    run = hold(p, obj, (), RUN_FRAMES, lx, ly, sample=True)
    if len(run) < 8: return None
    a, b = run[-8], run[-1]
    hx, hz = b[1] - a[1], b[2] - a[2]
    if math.hypot(hx, hz) < 0.3: return None        # never got moving: blocked start

    hold(p, obj, ("circle",), SLIDE_FRAMES, lx, ly)  # circle slides; cross at frame 12 of it is the slide jump
    x0, _, z0 = rig.pos(p)
    t0 = frame(p)
    s = hold(p, obj, ("circle", "cross"), JUMP_FRAMES, lx, ly, clock=t0, sample=True)
    s += hold(p, obj, (), AIR_FRAMES, lx, ly, clock=t0, sample=True)
    rig.set_pad(p)

    hs = [v[3] for v in s]
    peak = max(hs)
    if peak < 0.30: return None                     # never left the ground
    land = next((v for v in s[hs.index(peak):] if v[3] <= GROUND), None)
    if land is None: return None                    # still falling when the window ended
    dx, dz = land[1] - x0, land[2] - z0
    return dict(dist=math.hypot(dx, dz),
                dev=math.degrees(math.atan2(hx * dz - hz * dx, hx * dx + hz * dz)),
                height=peak, secs=land[5] - s[0][5])

def rate(p, secs=2.0):
    f0 = frame(p); t0 = time.time()
    while time.time() - t0 < secs: pass
    return (frame(p) - f0) / (time.time() - t0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state", help="state name to use (created if --warp is given)")
    ap.add_argument("--warp", help="level path to warp to first, e.g. Levels\\Earth\\Hub\\huba")
    ap.add_argument("--trials", type=int, default=4)
    o = ap.parse_args()

    if o.warp: rig.level(o.state, o.warp, fresh=True, timeout=120)
    p = rig.Pine()
    hz = rate(p)
    rows = []
    for _ in range(o.trials):
        rig.level(o.state)
        r = trial(rig.Pine())
        if r: rows.append(r)
    rig.set_pad(rig.Pine())
    if not rows: raise SystemExit("no clean jump - wrong level, blocked spawn, or the game is wedged")
    print(f"{o.state}: {hz:.2f} Hz, {len(rows)}/{o.trials} clean")
    for k, label in (("dist", "distance"), ("dev", "deviation deg"), ("height", "peak height"),
                     ("secs", "airtime s")):
        v = [r[k] for r in rows]
        print(f"  {label:14s} mean {sum(v)/len(v):8.3f}   range {min(v):8.3f} .. {max(v):8.3f}")

if __name__ == "__main__":
    main()

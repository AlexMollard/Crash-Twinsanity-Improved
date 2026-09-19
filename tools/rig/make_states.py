"""Builds the level state library (states/NAME.p2s) by warping through the credits from a base state.

  python make_states.py BASE NAME=PATH [NAME=PATH ...]

Levels that already have a state are skipped. Each warp takes ~2.5 minutes."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

base, *pairs = sys.argv[1:]
for pair in pairs:
    name, path = pair.split("=", 1)
    if os.path.exists(os.path.join(rig.STATES_DIR, name + ".p2s")): print(f"{name}: already have a state", flush=True); continue
    t0 = time.time()
    try:
        rig.level(base); rig.level(name, path)
        rig.screenshot(os.path.join(rig.HERE, "results", f"state_{name}.png"))
        x, y, z = rig.pos(rig.Pine()); print(f"{name}: ok in {time.time()-t0:.0f}s, crash at ({x:.1f}, {y:.1f}, {z:.1f})", flush=True)
    except SystemExit as e:
        print(f"{name}: FAILED ({e})", flush=True); rig.pine_reset()

"""Cutscene skip test: plays one cutscene twice from the same saved state - untouched, then holding Triangle -
and compares how long until Crash can move again, where he ends up, the game-flow state and screenshots.

  python cutscene_test.py NAME STATE X Z [--walk-timeout S] [--out DIR]

STATE is a states/<STATE>.p2s level state (see rig.py level); X Z is a point inside the cutscene's trigger."""
import argparse, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

def wait_control(p, timeout=180):
    """Seconds until pushing the stick moves Crash again."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        a = rig.pos(p); rig.set_pad(p, (), 0, -1); time.sleep(0.25); rig.set_pad(p); b = rig.pos(p)
        if math.dist(a, b) > 0.05: return time.time() - t0
        time.sleep(0.25)
    return None

def run(name, state, x, z, skip, out, walk_timeout):
    rig.level(state); p = rig.Pine()
    started = not rig.goto(x, z, 1.5, timeout=walk_timeout)
    if not started: return {"started": False}
    t0 = time.time()
    rig.screenshot(os.path.join(out, f"{name}_{'skip' if skip else 'full'}_start.png"))
    if skip:
        rig.set_pad(p, ("triangle",)); time.sleep(1.0); rig.set_pad(p)
    secs = wait_control(p)
    time.sleep(1.5)
    shot = os.path.join(out, f"{name}_{'skip' if skip else 'full'}_end.png"); rig.screenshot(shot)
    return {"started": True, "seconds": None if secs is None else round(time.time() - t0 - 1.5, 1),
            "pos": tuple(round(v, 2) for v in rig.pos(p)), "flow": rig.flow_state(p), "shot": shot}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("state"); ap.add_argument("x", type=float); ap.add_argument("z", type=float)
    ap.add_argument("--walk-timeout", type=float, default=60); ap.add_argument("--out", default=os.path.join(rig.HERE, "results"))
    o = ap.parse_args(); os.makedirs(o.out, exist_ok=True)
    full = run(o.name, o.state, o.x, o.z, False, o.out, o.walk_timeout)
    skip = run(o.name, o.state, o.x, o.z, True, o.out, o.walk_timeout)
    print(f"\n{o.name}:\n  full : {full}\n  skip : {skip}")
    if full.get("started") and skip.get("started"):
        same_pos = math.dist(full["pos"], skip["pos"]) < 1.0
        faster = skip["seconds"] is not None and full["seconds"] is not None and skip["seconds"] < full["seconds"] - 1
        verdict = "PASS" if (faster and same_pos and skip["flow"] == full["flow"]) else "CHECK"
        print(f"  => {verdict}: skip {'saved %.1fs' % (full['seconds'] - skip['seconds']) if faster else 'did not shorten it'}, "
              f"end position {'matches' if same_pos else 'DIFFERS'}, flow state {skip['flow']} vs {full['flow']}")

if __name__ == "__main__":
    main()

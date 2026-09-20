"""Cutscene skip test: plays one cutscene twice from the same level state - untouched, then holding Triangle -
and compares the time until gameplay resumes, where Crash ends up, the game-flow state and screenshots.

  python cutscene_test.py NAME STATE X Y Z [--out DIR]

STATE is a states/<STATE>.p2s level state (see rig.py level); X Y Z is the centre of the cutscene's trigger.
Crash is teleported into the trigger; a cutscene counts as started when the letterbox bars appear and as over
when they are gone and Crash responds to the stick again.

Each run also records whether what played was an in-engine `scene` or a pre-rendered `movie`, because the
letterbox alone cannot tell them apart and the two mean opposite things about a level recipe: the executable
already skips movies game-wide, so a movie's 55.7s -> 4.0s is a pass for a recipe that is doing nothing."""
import argparse, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

def controllable(p):
    a = rig.pos(p); rig.set_pad(p, (), 0, -1); time.sleep(0.2); rig.set_pad(p); b = rig.pos(p)
    return math.dist(a, b) > 0.05

def run(name, state, x, y, z, skip, out, start_timeout=12, end_timeout=240, progress=None):
    tag = "skip" if skip else "full"
    rig.level(state); p = rig.Pine()
    if progress is not None:                          # story-progress counter read by script condition 639
        a = p.r32(rig.FLOW_PTR) + 1284; p.w32(a, (p.r32(a) & ~(0x1F << 21)) | (progress << 21))
    rig.teleport(x, y + 1.0, z); t0 = time.time(); nudge = 0
    while not rig.in_cutscene():
        if time.time() - t0 > start_timeout:
            rig.screenshot(os.path.join(out, f"{name}_{tag}_nostart.png")); return {"started": False}
        if time.time() - t0 > 3 and nudge < 6:          # some triggers only react to movement
            rig.set_pad(p, (), [0.6, -0.6, 0, 0, 0.4, -0.4][nudge], [0, 0, 0.6, -0.6, 0.4, -0.4][nudge]); time.sleep(0.25); rig.set_pad(p); nudge += 1
        time.sleep(0.2)
    t_start = time.time(); rig.screenshot(os.path.join(out, f"{name}_{tag}_start.png"))
    kind = "movie" if rig.movie_playing(p) else "scene"   # both letterbox; only one of them a recipe can change
    if skip:
        time.sleep(1.0); rig.set_pad(p, ("triangle",)); time.sleep(1.5); rig.set_pad(p)
    while True:
        if time.time() - t_start > end_timeout:
            rig.screenshot(os.path.join(out, f"{name}_{tag}_stuck.png"))
            return {"started": True, "kind": kind, "seconds": None, "stuck": True, "flow": rig.flow_state(p)}
        if rig.movie_playing(p): kind = "movie"           # a movie can start a little after the letterbox does
        if not rig.in_cutscene() and controllable(p): break
        time.sleep(0.3)
    secs = round(time.time() - t_start, 1)
    time.sleep(2.0)
    shot = os.path.join(out, f"{name}_{tag}_end.png"); rig.screenshot(shot)
    return {"started": True, "kind": kind, "seconds": secs, "pos": tuple(round(v, 2) for v in rig.pos(p)), "flow": rig.flow_state(p),
            "cutscene_again": rig.in_cutscene(), "shot": shot}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("state")
    for c in "xyz": ap.add_argument(c, type=float)
    ap.add_argument("--out", default=os.path.join(rig.HERE, "results")); ap.add_argument("--skip-only", action="store_true"); ap.add_argument("--full-only", action="store_true"); ap.add_argument("--progress", type=int)
    o = ap.parse_args(); os.makedirs(o.out, exist_ok=True)
    full = {"started": None} if o.skip_only else run(o.name, o.state, o.x, o.y, o.z, False, o.out, progress=o.progress)
    skip = {"started": None} if o.full_only else run(o.name, o.state, o.x, o.y, o.z, True, o.out, progress=o.progress)
    print(f"\n{o.name}:\n  full : {full}\n  skip : {skip}")
    if o.full_only:
        print("  => " + ("NOT TRIGGERED" if not full.get("started") else "STUCK" if full.get("stuck") else f"PLAYS {full['seconds']}s")); return
    if not skip.get("started"): print("  => NOT TRIGGERED"); return
    if skip.get("stuck"): print("  => FAIL: still in the cutscene / no control after the skip"); return
    if not full.get("started") or full.get("stuck"): print(f"  => SKIP ONLY: gameplay back after {skip['seconds']}s"); return
    d = math.dist(full["pos"], skip["pos"])
    ok = skip["seconds"] < full["seconds"] - 1 and d < 3.0 and skip["flow"] == full["flow"] and not skip["cutscene_again"]
    print(f"  => {'PASS' if ok else 'CHECK'}: {full['seconds']}s -> {skip['seconds']}s, end position {d:.1f} apart, "
          f"flow {skip['flow']} vs {full['flow']}{', CUTSCENE RESUMED' if skip['cutscene_again'] else ''}")
    if "movie" in (full.get("kind"), skip.get("kind")):
        print("     MOVIE: these coordinates play a pre-rendered movie, which the executable's hold-Triangle "
              "already skips.\n     The result says nothing about a level recipe - only a 'scene' does.")

if __name__ == "__main__":
    main()
